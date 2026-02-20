"""
Income model — unified ledger for all income events.
Every income credit to a wallet creates one Income row.
"""
from django.db import models
from apps.core.models import TimeStampedModel


class Income(TimeStampedModel):
    """
    Single record per income event.
    Created by WalletService.credit_system() → IncomeService.record().
    """

    class IncomeType(models.TextChoices):
        REG_BONUS = 'reg_bonus', 'Registration Bonus'
        GENERATION = 'generation', 'Generation Income'
        GEN_MULTIPLIER = 'gen_multiplier', 'Generation Multiplier'
        MATCHING = 'matching', 'Matching Bonus'
        RANK_BONUS = 'rank_bonus', 'Rank Advancement Weekly Bonus'
        LEVEL_BOOSTER = 'level_booster', 'Level Income Booster'
        DAILY_ROI = 'daily_roi', 'Daily ROI'

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='incomes',
    )
    source_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incomes_generated',
        help_text='User whose activity triggered this income.',
    )
    income_type = models.CharField(max_length=16, choices=IncomeType.choices, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet_type = models.CharField(max_length=12, help_text='Which wallet was credited.')
    level = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='MLM level (1–20) for generation income.',
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Income'
        verbose_name_plural = 'Incomes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'income_type', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['source_user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} | {self.income_type} | ${self.amount}'
