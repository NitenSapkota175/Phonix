"""
Transaction model — unified ledger for all financial events.
Every wallet balance change (credit or debit) must produce a Transaction row.
"""
from decimal import Decimal
from django.db import models
from apps.core.models import TimeStampedModel


class Transaction(TimeStampedModel):
    """
    Immutable audit trail of all financial operations.
    Created by WalletService — never create directly in views.
    """

    class TxnType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        TRADE = 'trade', 'Trade Activation'
        SWAP = 'swap', 'Swap'
        TRANSFER = 'transfer', 'Internal Transfer'
        DAILY_ROI = 'daily_roi', 'Daily ROI'
        REG_BONUS = 'reg_bonus', 'Registration Bonus'
        GENERATION = 'generation', 'Generation Income'
        GEN_MULTIPLIER = 'gen_multiplier', 'Generation Multiplier'
        MATCHING = 'matching', 'Matching Bonus'
        RANK_BONUS = 'rank_bonus', 'Rank Bonus'
        LEVEL_BOOSTER = 'level_booster', 'Level Income Booster'

    class TxnStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    txn_type = models.CharField(max_length=16, choices=TxnType.choices, db_index=True)
    status = models.CharField(
        max_length=12, choices=TxnStatus.choices,
        default=TxnStatus.PENDING, db_index=True,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.TextField(blank=True)

    # Admin approval tracking
    approved_by = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_transactions',
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'txn_type', '-created_at']),
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['status', 'txn_type']),
            models.Index(fields=['wallet', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} | {self.txn_type} | ${self.amount} | {self.status}'
