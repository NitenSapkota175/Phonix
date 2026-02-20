"""
Rank models — 3-model architecture:
  Rank      — Definition (seeded via data migration)
  UserRank  — Active rank assignment per user
  RankPayout — Immutable payout ledger (prevents duplicates)

10 Ranks: Connector → Chief
Executive rank has asymmetric left/right targets.
"""
from decimal import Decimal
from django.db import models
from apps.core.models import TimeStampedModel


class Rank(TimeStampedModel):
    """
    Rank definition — seeded once via data migration.
    Admins should not edit these directly in production.
    """
    name = models.CharField(max_length=30, unique=True)
    level = models.PositiveSmallIntegerField(
        unique=True,
        help_text='Ordering: 1=Connector, 10=Chief',
    )
    left_target = models.DecimalField(max_digits=14, decimal_places=2)
    right_target = models.DecimalField(max_digits=14, decimal_places=2)
    weekly_bonus = models.DecimalField(max_digits=10, decimal_places=2)
    duration_weeks = models.PositiveSmallIntegerField(default=52)
    is_asymmetric = models.BooleanField(
        default=False,
        help_text='True for Executive — checks (L≥500k AND R≥100k) OR (R≥500k AND L≥100k).',
    )

    class Meta:
        verbose_name = 'Rank'
        verbose_name_plural = 'Ranks'
        ordering = ['level']

    def __str__(self):
        return f'{self.level}. {self.name} (${self.weekly_bonus}/week)'


class UserRank(TimeStampedModel):
    """
    Active rank assignment for a user.
    One row per rank ever achieved (unique_together enforces this).
    Once all 52 weeks are paid, is_active=False.
    """
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_ranks',
    )
    rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name='user_ranks')
    achieved_date = models.DateField()
    weeks_paid = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'User Rank'
        verbose_name_plural = 'User Ranks'
        unique_together = [('user', 'rank')]
        indexes = [
            models.Index(fields=['is_active', 'weeks_paid']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user.username} — {self.rank.name} ({self.weeks_paid}/52 weeks)'


class RankPayout(TimeStampedModel):
    """
    Immutable payout record — one row per user per rank per week.
    unique_together on (user, rank, week_number) prevents duplicate payouts.
    """
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='rank_payouts',
    )
    rank = models.ForeignKey(Rank, on_delete=models.PROTECT)
    week_number = models.PositiveSmallIntegerField(
        help_text='Week number 1–52 for this rank payout cycle.',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rank Payout'
        verbose_name_plural = 'Rank Payouts'
        unique_together = [('user', 'rank', 'week_number')]
        ordering = ['-paid_at']
        indexes = [
            models.Index(fields=['user', 'rank', '-paid_at']),
        ]

    def __str__(self):
        return f'{self.user.username} — {self.rank.name} Week {self.week_number} — ${self.amount}'
