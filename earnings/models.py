from django.db import models
from decimal import Decimal


class Commission(models.Model):
    """
    Track all commission payments in the MLM system.
    """
    
    GENERATION = 'generation'
    DAILY_BOND = 'daily_bond'
    
    TYPE_CHOICES = [
        (GENERATION, 'Generation Income'),
        (DAILY_BOND, 'Daily Bond Income'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='commissions_received',
        help_text="User receiving the commission"
    )
    from_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='commissions_generated',
        help_text="User whose activity generated this commission"
    )
    
    level = models.IntegerField(
        help_text="Level in MLM structure (1-20 for generation income, 0 for daily bond)"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    commission_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )
    
    # Source tracking
    source_subscription = models.ForeignKey(
        'investment.Subscription',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commissions'
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Additional details about the commission"
    )
    
    paid_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Commission'
        verbose_name_plural = 'Commissions'
        ordering = ['-paid_at']
        indexes = [
            models.Index(fields=['user', '-paid_at']),
            models.Index(fields=['from_user', '-paid_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level} - ${self.amount}"


# Commission rates for 20-level MLM structure
COMMISSION_RATES = {
    1: Decimal('0.10'),   # 10%
    2: Decimal('0.05'),   # 5%
    3: Decimal('0.03'),   # 3%
    4: Decimal('0.02'),   # 2%
    5: Decimal('0.02'),   # 2%
    6: Decimal('0.01'),   # 1%
    7: Decimal('0.01'),   # 1%
    8: Decimal('0.01'),   # 1%
    9: Decimal('0.01'),   # 1%
    10: Decimal('0.01'),  # 1%
    11: Decimal('0.005'), # 0.5%
    12: Decimal('0.005'), # 0.5%
    13: Decimal('0.005'), # 0.5%
    14: Decimal('0.005'), # 0.5%
    15: Decimal('0.005'), # 0.5%
    16: Decimal('0.003'), # 0.3%
    17: Decimal('0.003'), # 0.3%
    18: Decimal('0.003'), # 0.3%
    19: Decimal('0.003'), # 0.3%
    20: Decimal('0.003'), # 0.3%
}

# Direct referral requirements for each level
DIRECT_REQUIREMENTS = {
    1: 0,   # No requirement for Level 1
    2: 0,   # No requirement for Level 2
    3: 2,   # Level 3 requires 2 direct referrals
    4: 2,
    5: 3,   # Level 5 requires 3 directs
    6: 3,
    7: 4,
    8: 4,
    9: 5,
    10: 5,
    11: 6,
    12: 6,
    13: 7,
    14: 7,
    15: 8,
    16: 8,
    17: 9,
    18: 9,
    19: 10,
    20: 10,
}
