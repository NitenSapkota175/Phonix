"""
Custom User model for the Phonix platform.

Key changes from the original:
- Removed: wallet_balance, registration_bonus, total_earnings, total_invested
  (these now live in apps.wallets.Wallet)
- Added: transaction_password, is_email_verified, role, phone
- Kept: referral_code, referred_by, direct_referrals_count, is_active_investor
- Binary tree structure lives in apps.referral.BinaryNode (OneToOne to User)
"""
import string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

from apps.core.models import TimeStampedModel


class User(AbstractUser):
    """
    Phonix platform user.
    Extends AbstractUser with MLM, authentication, and role fields.
    """

    class Role(models.TextChoices):
        USER = 'user', 'User'
        SUPPORT = 'support', 'Support Staff'
        ADMIN = 'admin', 'Administrator'

    # ─── MLM Fields ───────────────────────────────────────────────────────────
    referred_by = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='direct_referrals',
        help_text='The user who referred this user (sponsor).',
    )
    referral_code = models.CharField(
        max_length=10, unique=True, blank=True,
        help_text='Unique referral code for sharing.',
    )
    direct_referrals_count = models.PositiveIntegerField(
        default=0,
        help_text='Cached count of direct referrals (Level 1). Updated by signal.',
    )
    is_active_investor = models.BooleanField(
        default=False,
        help_text='True if user has at least one active trade package.',
    )

    # ─── Authentication Extensions ────────────────────────────────────────────
    transaction_password = models.CharField(
        max_length=128, blank=True,
        help_text='Hashed secondary password required for financial operations.',
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text='True after user confirms their email address.',
    )

    # ─── Profile Fields ───────────────────────────────────────────────────────
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    phone = models.CharField(max_length=20, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['referral_code']),
            models.Index(fields=['referred_by']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f'{self.username} ({self.email})'

    # ─── Save Hook ────────────────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_unique_referral_code()
        super().save(*args, **kwargs)

    # ─── Referral Code ────────────────────────────────────────────────────────

    @staticmethod
    def _generate_unique_referral_code(length=8):
        allowed = string.ascii_uppercase + string.digits
        while True:
            code = get_random_string(length=length, allowed_chars=allowed)
            if not User.objects.filter(referral_code=code).exists():
                return code

    def get_referral_link(self, request):
        """Build full absolute referral URL."""
        from django.urls import reverse
        register_url = request.build_absolute_uri(reverse('accounts:register'))
        return f'{register_url}?ref={self.referral_code}'

    # ─── Role Helpers ─────────────────────────────────────────────────────────

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_staff

    @property
    def is_support_role(self):
        return self.role in (self.Role.SUPPORT, self.Role.ADMIN) or self.is_staff

    # ─── Transaction Password ─────────────────────────────────────────────────

    def set_transaction_password(self, raw_password):
        """Hash and store the transaction password."""
        from django.contrib.auth.hashers import make_password
        self.transaction_password = make_password(raw_password)

    def check_transaction_password(self, raw_password):
        """Verify the raw password against the stored hash."""
        from django.contrib.auth.hashers import check_password
        if not self.transaction_password:
            return False
        return check_password(raw_password, self.transaction_password)


class EmailVerificationToken(TimeStampedModel):
    """One-time email verification token."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_token')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Email Verification Token'

    def __str__(self):
        return f'{self.user.email} — verified={self.is_used}'

    @property
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
