"""
Wallet models — Main Wallet, Trade Wallet, Affiliate Wallet.

Each user gets exactly 3 wallet rows created at registration (via signal).
Balances are NEVER updated directly on the model — use WalletService.
"""
from decimal import Decimal

from django.db import models

from apps.core.models import TimeStampedModel


class Wallet(TimeStampedModel):
    """
    Multi-wallet row per user.
    One row per WalletType per user (enforced by unique_together).
    """

    class WalletType(models.TextChoices):
        MAIN = 'main', 'Main Wallet'
        TRADE = 'trade', 'Trade Wallet'
        AFFILIATE = 'affiliate', 'Affiliate Wallet'

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='wallets',
    )
    wallet_type = models.CharField(
        max_length=12,
        choices=WalletType.choices,
        db_index=True,
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Current available balance. Updated only via F() expressions.',
    )
    total_deposited = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
    )
    total_withdrawn = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
    )
    total_earned = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        help_text='Lifetime earnings credited to this wallet.',
    )
    earnings_cap = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        help_text='Max earnings = 3X active trade amount. 0 means no cap.',
    )

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        unique_together = [('user', 'wallet_type')]
        indexes = [
            models.Index(fields=['user', 'wallet_type']),
        ]

    def __str__(self):
        return f'{self.user.username} – {self.get_wallet_type_display()} (${self.balance})'

    @property
    def has_earnings_cap(self):
        return self.earnings_cap > 0

    @property
    def remaining_cap(self):
        """How much more can be earned before hitting the 3X cap."""
        if not self.has_earnings_cap:
            return None
        remaining = self.earnings_cap - self.total_earned
        return max(remaining, Decimal('0.00'))

    @property
    def cap_reached(self):
        if not self.has_earnings_cap:
            return False
        return self.total_earned >= self.earnings_cap
