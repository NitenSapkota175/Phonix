from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class Subscription(models.Model):
    """
    Investment subscription packages with tiered monthly returns.
    
    Tiers:
    - Tier 1: $50 - $3,000 (6% Monthly)
    - Tier 2: $3,001 - $5,000 (8% Monthly)
    - Tier 3: $5,001+ (10% Monthly)
    """
    
    TIER_1 = 'tier_1'
    TIER_2 = 'tier_2'
    TIER_3 = 'tier_3'
    
    TIER_CHOICES = [
        (TIER_1, 'Tier 1 ($50-$3,000 @ 6%)'),
        (TIER_2, 'Tier 2 ($3,001-$5,000 @ 8%)'),
        (TIER_3, 'Tier 3 ($5,001+ @ 10%)'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Investment amount"
    )
    tier = models.CharField(
        max_length=10,
        choices=TIER_CHOICES,
        help_text="Auto-calculated based on amount"
    )
    monthly_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Monthly return rate (e.g., 6.00 for 6%)"
    )
    
    # Earnings tracking
    total_earned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount earned from this subscription"
    )
    earnings_cap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum earnings (3x the amount)"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Active subscriptions earn daily bond income"
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When subscription was purchased"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When subscription reached 3x cap"
    )
    
    # Bonus tracking
    bonus_used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount of registration bonus used for this purchase"
    )
    
    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.tier} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate tier, rate, and earnings cap on save"""
        if not self.tier or not self.monthly_rate:
            self.tier, self.monthly_rate = self.calculate_tier_and_rate()
        
        if not self.earnings_cap:
            self.earnings_cap = self.amount * 3
        
        super().save(*args, **kwargs)
    
    def calculate_tier_and_rate(self):
        """Determine tier and monthly rate based on amount"""
        if self.amount < 50:
            raise ValidationError("Minimum investment is $50")
        elif self.amount <= 3000:
            return self.TIER_1, Decimal('6.00')
        elif self.amount <= 5000:
            return self.TIER_2, Decimal('8.00')
        else:
            return self.TIER_3, Decimal('10.00')
    
    def calculate_daily_income(self):
        """
        Calculate daily bond income.
        Formula: (amount * monthly_rate / 100) / 30 days
        """
        monthly_income = (self.amount * self.monthly_rate) / 100
        daily_income = monthly_income / 30
        return daily_income
    
    def can_earn(self, amount):
        """Check if subscription can earn the specified amount without exceeding cap"""
        return (self.total_earned + amount) <= self.earnings_cap
    
    def get_remaining_earnings_capacity(self):
        """Get how much more this subscription can earn"""
        remaining = self.earnings_cap - self.total_earned
        return max(remaining, Decimal('0.00'))
    
    def add_earnings(self, amount):
        """
        Add earnings to this subscription and check if cap is reached.
        Returns the actual amount added (may be less if cap is reached).
        """
        remaining_capacity = self.get_remaining_earnings_capacity()
        actual_amount = min(amount, remaining_capacity)
        
        self.total_earned += actual_amount
        
        # Check if cap is reached
        if self.total_earned >= self.earnings_cap:
            self.is_active = False
            self.completed_at = timezone.now()
        
        self.save()
        return actual_amount
    
    @property
    def earnings_percentage(self):
        """Calculate percentage of earnings cap reached"""
        if self.earnings_cap == 0:
            return 0
        return (self.total_earned / self.earnings_cap) * 100
    
    @property
    def days_active(self):
        """Number of days subscription has been active"""
        if self.completed_at:
            return (self.completed_at - self.started_at).days
        return (timezone.now() - self.started_at).days
