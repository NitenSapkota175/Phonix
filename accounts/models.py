from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string
import string


class User(AbstractUser):
    """
    Custom User model for Phonix MLM platform.
    Extends Django's AbstractUser with wallet and MLM-specific fields.
    """
    
    # Wallet fields
    wallet_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Main wallet balance for deposits and withdrawals"
    )
    registration_bonus = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Registration bonus (max $10, can only use 10% for subscription)"
    )
    
    # MLM structure fields
    referred_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals',
        help_text="User who referred this user"
    )
    referral_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        help_text="Unique referral code for sharing"
    )
    
    # Tracking fields
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total earnings from all sources (for 3x cap calculation)"
    )
    total_invested = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total amount invested in subscriptions"
    )
    direct_referrals_count = models.IntegerField(
        default=0,
        help_text="Number of direct referrals (Level 1)"
    )
    
    # Status fields
    is_active_investor = models.BooleanField(
        default=False,
        help_text="True if user has at least one active subscription"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when user registered"
    )
    
    # TRC20 wallet address
    trc20_wallet_address = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="User's TRC20 USDT wallet address for withdrawals"
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def save(self, *args, **kwargs):
        """Generate unique referral code on first save"""
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_referral_code(length=8):
        """Generate a unique alphanumeric referral code"""
        while True:
            # Generate random alphanumeric code (uppercase letters and digits)
            code = ''.join(get_random_string(
                length=length,
                allowed_chars=string.ascii_uppercase + string.digits
            ))
            # Ensure uniqueness
            if not User.objects.filter(referral_code=code).exists():
                return code
    
    def get_referral_link(self, request=None):
        """Generate full referral link"""
        if request:
            base_url = request.build_absolute_uri('/')[:-1]
        else:
            base_url = "http://localhost:8000"  # Default for development
        return f"{base_url}/register?ref={self.referral_code}"
    
    def can_receive_commission(self, amount):
        """
        Check if user can receive commission based on 3x earnings cap.
        Total earnings cannot exceed 3x total invested.
        """
        if self.total_invested == 0:
            return False
        
        max_earnings = self.total_invested * 3
        return (self.total_earnings + amount) <= max_earnings
    
    def get_available_commission_amount(self):
        """Get remaining amount user can earn before hitting 3x cap"""
        if self.total_invested == 0:
            return 0
        
        max_earnings = self.total_invested * 3
        remaining = max_earnings - self.total_earnings
        return max(remaining, 0)
    
    def update_direct_referrals_count(self):
        """Update the count of direct referrals"""
        self.direct_referrals_count = self.referrals.count()
        self.save(update_fields=['direct_referrals_count'])
    
    @property
    def total_balance(self):
        """Total available balance (wallet + registration bonus)"""
        return self.wallet_balance + self.registration_bonus
    
    @property
    def earnings_cap_percentage(self):
        """Calculate percentage of earnings cap reached"""
        if self.total_invested == 0:
            return 0
        
        max_earnings = self.total_invested * 3
        if max_earnings == 0:
            return 0
        
        percentage = (self.total_earnings / max_earnings) * 100
        return min(percentage, 100)
