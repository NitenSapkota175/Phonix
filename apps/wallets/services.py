"""
WalletService — all financial operations for user wallets.

Rules enforced here:
- All balance changes use F() expressions (no race conditions)
- select_for_update() used on every balance operation (row-level locking)
- All operations wrapped in atomic transactions
- Earnings cap enforced
- Withdrawal: min $10, 5% fee, 24h rate limit
- Swap only allowed: Main → Trade
- Internal transfer only between user's own wallets
"""
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.core.exceptions import (
    InsufficientBalanceError,
    CapExceededError,
    WithdrawalRateLimitError,
    MinimumWithdrawalError,
    InvalidWalletOperationError,
)
from .models import Wallet


class WalletService:
    """
    Central service for all wallet operations.
    Never update Wallet.balance directly — always go through this service.
    """

    # ─── Initialization ───────────────────────────────────────────────────────

    @staticmethod
    def initialize_user_wallets(user):
        """
        Create 3 wallet rows for a newly registered user.
        Called from apps/accounts/signals.py on user creation.
        """
        for wallet_type in Wallet.WalletType.values:
            Wallet.objects.get_or_create(user=user, wallet_type=wallet_type)

    @staticmethod
    def get_wallet(user, wallet_type: str, lock=False) -> Wallet:
        """
        Retrieve a wallet, optionally with a row-level lock.
        Always call inside an atomic block when lock=True.
        """
        qs = Wallet.objects.filter(user=user, wallet_type=wallet_type)
        if lock:
            qs = qs.select_for_update()
        return qs.get()

    # ─── Credit (Internal — income, bonuses, ROI) ─────────────────────────────

    @staticmethod
    def credit_system(user, wallet_type: str, amount, txn_type: str, description: str = '', source_user=None):
        """
        Credit a system-generated income to a wallet (ROI, bonus, income, etc.).
        Respects earnings cap for Main and Trade wallets.
        Uses F() expression for atomic balance update.

        Returns the actual amount credited (may be less if cap applies).
        """
        amount = Decimal(str(amount))
        if amount <= 0:
            return Decimal('0.00')

        with transaction.atomic():
            wallet = WalletService.get_wallet(user, wallet_type, lock=True)

            # Enforce earnings cap where applicable
            actual_amount = amount
            if wallet.has_earnings_cap:
                remaining = wallet.remaining_cap
                if remaining <= 0:
                    raise CapExceededError(f'Earnings cap reached for {wallet.get_wallet_type_display()}.')
                actual_amount = min(amount, remaining)

            # Atomic balance credit
            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F('balance') + actual_amount,
                total_earned=F('total_earned') + actual_amount,
            )

            # Record transaction
            from apps.transactions.models import Transaction
            Transaction.objects.create(
                user=user,
                wallet=wallet,
                txn_type=txn_type,
                status=Transaction.TxnStatus.COMPLETED,
                amount=actual_amount,
                fee=Decimal('0.00'),
                net_amount=actual_amount,
                description=description,
            )

            # Record income
            from apps.incomes.services import IncomeService
            IncomeService.record(
                user=user,
                income_type=txn_type,
                amount=actual_amount,
                wallet_type=wallet_type,
                source_user=source_user,
                description=description,
            )

            return actual_amount

    # ─── Debit (Trade purchase, swap source) ──────────────────────────────────

    @staticmethod
    def debit(user, wallet_type: str, amount, txn_type: str, description: str = ''):
        """
        Debit from a wallet.
        Raises InsufficientBalanceError if funds are insufficient.
        """
        amount = Decimal(str(amount))

        with transaction.atomic():
            wallet = WalletService.get_wallet(user, wallet_type, lock=True)
            wallet.refresh_from_db()   # re-read after lock

            if wallet.balance < amount:
                raise InsufficientBalanceError(
                    f'Insufficient {wallet.get_wallet_type_display()} balance. '
                    f'Required: ${amount}, Available: ${wallet.balance}'
                )

            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F('balance') - amount,
                total_withdrawn=F('total_withdrawn') + amount,
            )

            from apps.transactions.models import Transaction
            Transaction.objects.create(
                user=user,
                wallet=wallet,
                txn_type=txn_type,
                status=Transaction.TxnStatus.COMPLETED,
                amount=amount,
                fee=Decimal('0.00'),
                net_amount=amount,
                description=description,
            )

    # ─── Deposit (Admin-approval flow) ────────────────────────────────────────

    @staticmethod
    def request_deposit(user, amount, reference: str = ''):
        """
        Create a pending deposit transaction.
        Admin approves via admin panel → calls approve_deposit().
        """
        amount = Decimal(str(amount))
        if amount <= 0:
            raise InvalidWalletOperationError('Deposit amount must be positive.')

        wallet = WalletService.get_wallet(user, Wallet.WalletType.MAIN)

        from apps.transactions.models import Transaction
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            txn_type=Transaction.TxnType.DEPOSIT,
            status=Transaction.TxnStatus.PENDING,
            amount=amount,
            fee=Decimal('0.00'),
            net_amount=amount,
            description=f'Deposit request. Reference: {reference}',
        )
        return txn

    @staticmethod
    def approve_deposit(transaction_obj, approved_by):
        """
        Admin approves a pending deposit — credits Main Wallet atomically.
        """
        from apps.transactions.models import Transaction
        with transaction.atomic():
            txn = Transaction.objects.select_for_update().get(pk=transaction_obj.pk)

            if txn.status != Transaction.TxnStatus.PENDING:
                raise InvalidWalletOperationError('Only pending deposits can be approved.')

            wallet = WalletService.get_wallet(txn.user, Wallet.WalletType.MAIN, lock=True)

            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F('balance') + txn.net_amount,
                total_deposited=F('total_deposited') + txn.net_amount,
            )

            Transaction.objects.filter(pk=txn.pk).update(
                status=Transaction.TxnStatus.COMPLETED,
                approved_by=approved_by,
                approved_at=timezone.now(),
            )

    # ─── Withdrawal ───────────────────────────────────────────────────────────

    @staticmethod
    def request_withdrawal(user, amount, transaction_password: str):
        """
        Request a withdrawal from Main Wallet.
        - Verifies transaction password
        - Enforces $10 minimum
        - Enforces 5% fee
        - Rate limits: 1 per 24h
        - Deducts balance immediately (reserved)
        - Creates pending withdrawal transaction for admin approval
        """
        from apps.accounts.services import AccountService
        AccountService.verify_transaction_password(user, transaction_password)

        amount = Decimal(str(amount))
        min_amount = Decimal(str(settings.WITHDRAWAL_MIN_AMOUNT))
        if amount < min_amount:
            raise MinimumWithdrawalError(f'Minimum withdrawal is ${min_amount}.')

        # Rate limit check
        rate_limit_key = f'withdrawal_rl:{user.pk}'
        if cache.get(rate_limit_key):
            raise WithdrawalRateLimitError()

        fee_pct = Decimal(str(settings.WITHDRAWAL_FEE_PERCENT))
        fee = (amount * fee_pct).quantize(Decimal('0.01'))
        net_amount = amount - fee

        with transaction.atomic():
            wallet = WalletService.get_wallet(user, Wallet.WalletType.MAIN, lock=True)
            wallet.refresh_from_db()

            if wallet.balance < amount:
                raise InsufficientBalanceError(
                    f'Insufficient balance. Required: ${amount}, Available: ${wallet.balance}'
                )

            # Deduct immediately (funds reserved)
            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F('balance') - amount,
                total_withdrawn=F('total_withdrawn') + amount,
            )

            from apps.transactions.models import Transaction
            txn = Transaction.objects.create(
                user=user,
                wallet=wallet,
                txn_type=Transaction.TxnType.WITHDRAWAL,
                status=Transaction.TxnStatus.PENDING,
                amount=amount,
                fee=fee,
                net_amount=net_amount,
                description=f'Withdrawal request. Fee: ${fee} (5%)',
            )

        # Set rate limit in Redis (24 hours)
        limit_hours = getattr(settings, 'WITHDRAWAL_RATE_LIMIT_HOURS', 24)
        cache.set(rate_limit_key, True, timeout=limit_hours * 3600)

        return txn

    @staticmethod
    def approve_withdrawal(transaction_obj, approved_by):
        """Admin marks an approved withdrawal as completed."""
        from apps.transactions.models import Transaction
        Transaction.objects.filter(pk=transaction_obj.pk).update(
            status=Transaction.TxnStatus.COMPLETED,
            approved_by=approved_by,
            approved_at=timezone.now(),
        )

    @staticmethod
    def reject_withdrawal(transaction_obj, approved_by):
        """
        Admin rejects a withdrawal — refunds the deducted amount back to wallet.
        """
        from apps.transactions.models import Transaction
        with transaction.atomic():
            txn = Transaction.objects.select_for_update().get(pk=transaction_obj.pk)
            if txn.status != Transaction.TxnStatus.PENDING:
                raise InvalidWalletOperationError('Only pending withdrawals can be rejected.')

            # Refund
            Wallet.objects.filter(pk=txn.wallet_id).update(
                balance=F('balance') + txn.amount,
                total_withdrawn=F('total_withdrawn') - txn.amount,
            )
            Transaction.objects.filter(pk=txn.pk).update(
                status=Transaction.TxnStatus.CANCELLED,
                approved_by=approved_by,
                approved_at=timezone.now(),
                description=txn.description + '\n[REJECTED — funds refunded]',
            )

    # ─── Swap (Main → Trade only) ─────────────────────────────────────────────

    @staticmethod
    def swap(user, amount, transaction_password: str):
        """
        Swap funds from Main Wallet to Trade Wallet.
        Direction is always Main → Trade.
        Verifies transaction password.
        """
        from apps.accounts.services import AccountService
        AccountService.verify_transaction_password(user, transaction_password)

        amount = Decimal(str(amount))
        if amount <= 0:
            raise InvalidWalletOperationError('Swap amount must be positive.')

        with transaction.atomic():
            main_wallet = WalletService.get_wallet(user, Wallet.WalletType.MAIN, lock=True)
            trade_wallet = WalletService.get_wallet(user, Wallet.WalletType.TRADE, lock=True)

            main_wallet.refresh_from_db()
            if main_wallet.balance < amount:
                raise InsufficientBalanceError(
                    f'Insufficient Main Wallet balance. Available: ${main_wallet.balance}'
                )

            # Deduct from Main
            Wallet.objects.filter(pk=main_wallet.pk).update(balance=F('balance') - amount)
            # Credit to Trade
            Wallet.objects.filter(pk=trade_wallet.pk).update(balance=F('balance') + amount)

            from apps.transactions.models import Transaction
            Transaction.objects.create(
                user=user, wallet=main_wallet,
                txn_type=Transaction.TxnType.SWAP,
                status=Transaction.TxnStatus.COMPLETED,
                amount=amount, fee=Decimal('0.00'), net_amount=amount,
                description=f'Swap ${amount} from Main Wallet to Trade Wallet',
            )

    # ─── Internal Transfer ────────────────────────────────────────────────────

    @staticmethod
    def internal_transfer(user, from_wallet_type: str, to_wallet_type: str, amount, transaction_password: str):
        """Transfer between the user's own wallets."""
        from apps.accounts.services import AccountService
        AccountService.verify_transaction_password(user, transaction_password)

        if from_wallet_type == to_wallet_type:
            raise InvalidWalletOperationError('Cannot transfer between the same wallet.')

        amount = Decimal(str(amount))
        if amount <= 0:
            raise InvalidWalletOperationError('Transfer amount must be positive.')

        with transaction.atomic():
            from_w = WalletService.get_wallet(user, from_wallet_type, lock=True)
            to_w = WalletService.get_wallet(user, to_wallet_type, lock=True)

            from_w.refresh_from_db()
            if from_w.balance < amount:
                raise InsufficientBalanceError(f'Insufficient {from_w.get_wallet_type_display()} balance.')

            Wallet.objects.filter(pk=from_w.pk).update(balance=F('balance') - amount)
            Wallet.objects.filter(pk=to_w.pk).update(balance=F('balance') + amount)

            from apps.transactions.models import Transaction
            Transaction.objects.create(
                user=user, wallet=from_w,
                txn_type=Transaction.TxnType.TRANSFER,
                status=Transaction.TxnStatus.COMPLETED,
                amount=amount, fee=Decimal('0.00'), net_amount=amount,
                description=f'Transfer ${amount} from {from_w.get_wallet_type_display()} to {to_w.get_wallet_type_display()}',
            )

    # ─── Earnings Cap Management ──────────────────────────────────────────────

    @staticmethod
    def update_earnings_cap(user, wallet_type: str, new_cap: Decimal):
        """
        Update the earnings cap for a wallet (called when user activates a trade).
        Cap = 3 × trade amount.
        """
        Wallet.objects.filter(user=user, wallet_type=wallet_type).update(
            earnings_cap=new_cap,
        )
