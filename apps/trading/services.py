"""
TradeService — business logic for trade activation and daily ROI distribution.
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.core.exceptions import MinimumTradeAmountError, InvalidWalletOperationError
from apps.wallets.models import Wallet
from apps.wallets.services import WalletService
from .models import Trade


class TradeService:

    @staticmethod
    def activate(user, amount, transaction_password: str) -> Trade:
        """
        Activate a trade package:
        1. Verify transaction password
        2. Determine tier
        3. Debit from Trade Wallet
        4. Create Trade record
        5. Update Trade Wallet earnings cap = 3× amount
        6. Mark user as active investor
        7. Trigger generation income distribution (async, via Celery)
        """
        from apps.accounts.services import AccountService
        AccountService.verify_transaction_password(user, transaction_password)

        amount = Decimal(str(amount))
        try:
            tier, monthly_rate = Trade.resolve_tier(amount)
        except ValueError as exc:
            raise MinimumTradeAmountError(str(exc))

        earnings_cap = amount * Decimal('3')

        with transaction.atomic():
            # Deduct from Trade Wallet (WalletService handles lock + F())
            WalletService.debit(
                user=user,
                wallet_type=Wallet.WalletType.TRADE,
                amount=amount,
                txn_type='trade',
                description=f'Trade activation — {tier} @ ${amount}',
            )

            # Create Trade record
            trade = Trade.objects.create(
                user=user,
                amount=amount,
                tier=tier,
                monthly_rate=monthly_rate,
                earnings_cap=earnings_cap,
            )

            # Update earnings cap on Trade Wallet
            WalletService.update_earnings_cap(user, Wallet.WalletType.TRADE, earnings_cap)

            # Mark as active investor
            from apps.accounts.models import User
            User.objects.filter(pk=user.pk).update(is_active_investor=True)

        # Trigger 20-level generation income (async task)
        from apps.referral.tasks import distribute_generation_income
        distribute_generation_income.delay(trade.id)

        return trade

    @staticmethod
    def process_daily_roi():
        """
        Called by Celery Beat task Mon–Fri.
        Distributes daily ROI to all active trades.
        Uses F() and select_for_update() for atomic updates.

        Returns summary dict for task logging.
        """
        from apps.core.utils import is_business_day

        if not is_business_day():
            return {'status': 'skipped', 'reason': 'weekend'}

        active_trades = (
            Trade.objects
            .select_related('user')
            .filter(is_active=True)
            .select_for_update(skip_locked=True)  # skip any locked rows
        )

        processed = 0
        skipped = 0
        total_amount = Decimal('0.00')

        with transaction.atomic():
            for trade in active_trades:
                daily = trade.daily_roi
                remaining = trade.remaining_cap

                if remaining <= 0:
                    # Cap reached — deactivate
                    Trade.objects.filter(pk=trade.pk).update(
                        is_active=False,
                        completed_at=timezone.now(),
                    )
                    skipped += 1
                    continue

                actual = min(daily, remaining)

                try:
                    credited = WalletService.credit_system(
                        user=trade.user,
                        wallet_type=Wallet.WalletType.TRADE,
                        amount=actual,
                        txn_type='daily_roi',
                        description=f'Daily ROI for trade #{trade.pk}',
                    )
                    # Update trade earnings
                    Trade.objects.filter(pk=trade.pk).update(
                        total_earned=F('total_earned') + credited,
                    )
                    # Check if cap is now reached
                    trade.refresh_from_db(fields=['total_earned'])
                    if trade.total_earned >= trade.earnings_cap:
                        Trade.objects.filter(pk=trade.pk).update(
                            is_active=False, completed_at=timezone.now(),
                        )

                    total_amount += credited
                    processed += 1
                except Exception:
                    skipped += 1
                    continue

        return {
            'status': 'completed',
            'processed': processed,
            'skipped': skipped,
            'total_roi_distributed': str(total_amount),
        }
