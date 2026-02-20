"""
Trading models — tiered packages and active trade tracking.

Package Tiers:
    Tier 1: $50–$3,000   → 6%/month
    Tier 2: $3,001–$5,000 → 8%/month
    Tier 3: $5,001+       → 10%/month

ROI distributes Mon–Fri daily.
Earnings cap = 3× trade amount.
"""
from decimal import Decimal
from django.db import models
from apps.core.models import TimeStampedModel


class Trade(TimeStampedModel):
    """
    Active trade package for a user.
    Deducted from Trade Wallet on activation.
    Daily ROI credited to Trade Wallet (Mon–Fri).
    Stops when total_earned >= earnings_cap (3X amount).
    """

    class Tier(models.TextChoices):
        TIER_1 = 'tier_1', 'Tier 1 ($50–$3,000 @ 6%/month)'
        TIER_2 = 'tier_2', 'Tier 2 ($3,001–$5,000 @ 8%/month)'
        TIER_3 = 'tier_3', 'Tier 3 ($5,001+ @ 10%/month)'

    TIER_CONFIG = {
        Tier.TIER_1: {'min': Decimal('50'), 'max': Decimal('3000'), 'rate': Decimal('6.00')},
        Tier.TIER_2: {'min': Decimal('3001'), 'max': Decimal('5000'), 'rate': Decimal('8.00')},
        Tier.TIER_3: {'min': Decimal('5001'), 'max': None, 'rate': Decimal('10.00')},
    }

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='trades',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tier = models.CharField(max_length=8, choices=Tier.choices)
    monthly_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='Monthly ROI rate (e.g. 6.00 for 6%)',
    )
    total_earned = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Total ROI earned so far from this trade.',
    )
    earnings_cap = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='3× amount — trade stops earning beyond this.',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        ordering = ['-activated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active', '-activated_at']),
        ]

    def __str__(self):
        return f'{self.user.username} | {self.tier} | ${self.amount} | active={self.is_active}'

    @property
    def daily_roi(self) -> Decimal:
        """Daily ROI amount = (amount × monthly_rate / 100) / 30"""
        monthly = (self.amount * self.monthly_rate) / Decimal('100')
        return (monthly / Decimal('30')).quantize(Decimal('0.0001'))

    @property
    def remaining_cap(self) -> Decimal:
        return max(self.earnings_cap - self.total_earned, Decimal('0.00'))

    @staticmethod
    def resolve_tier(amount: Decimal):
        """
        Return (tier, monthly_rate) for a given investment amount.
        Raises ValueError if below minimum.
        """
        amount = Decimal(str(amount))
        if amount < Decimal('50'):
            raise ValueError('Minimum trade amount is $50.')
        if amount <= Decimal('3000'):
            return Trade.Tier.TIER_1, Decimal('6.00')
        if amount <= Decimal('5000'):
            return Trade.Tier.TIER_2, Decimal('8.00')
        return Trade.Tier.TIER_3, Decimal('10.00')
