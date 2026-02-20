"""
Accounts service layer — registration, authentication helpers, email verification.
"""
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone

from apps.core.exceptions import (
    InvalidTransactionPasswordError,
    InvalidOperationError,
    SelfReferralError,
)
from .models import User, EmailVerificationToken


class AccountService:
    """
    Handles registration, email verification, and password operations.
    All business logic stays OUT of views.
    """

    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        referral_code: str = None,
        phone: str = '',
    ) -> User:
        """
        Create a new user, link referral, create 3 wallets, place in binary tree.

        Steps:
        1. Validate referral code
        2. Create User
        3. Send email verification
        4. Create wallets (deferred to WalletService.initialize_user_wallets)
        5. Place in binary tree (deferred to ReferralService.on_user_registered)
        6. Award registration bonus
        """
        from django.db import transaction

        sponsor = None
        if referral_code:
            try:
                sponsor = User.objects.get(referral_code=referral_code)
            except User.DoesNotExist:
                raise InvalidOperationError('Invalid referral code.')

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                phone=phone,
                referred_by=sponsor,
                is_email_verified=False,
            )

            # Send verification email
            AccountService.send_verification_email(user)

            # Initialize wallets and referral placement are triggered via signals
            # (see apps/accounts/signals.py → post_save on User)

        return user

    @staticmethod
    def send_verification_email(user: User):
        """Generate token and send verification email."""
        from django.core.mail import send_mail
        from django.conf import settings

        # Invalidate old tokens
        EmailVerificationToken.objects.filter(user=user).delete()

        token_str = secrets.token_urlsafe(48)
        token = EmailVerificationToken.objects.create(
            user=user,
            token=token_str,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        verify_url = f"{settings.SITE_URL}/accounts/verify-email/{token_str}/"
        send_mail(
            subject=f'Verify your {settings.SITE_NAME} account',
            message=(
                f'Hi {user.username},\n\n'
                f'Click the link below to verify your email:\n{verify_url}\n\n'
                f'This link expires in 24 hours.\n\nThe {settings.SITE_NAME} Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return token

    @staticmethod
    def verify_email(token_str: str) -> User:
        """Mark user email as verified using token."""
        try:
            token = EmailVerificationToken.objects.select_related('user').get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            raise InvalidOperationError('Invalid or expired verification link.')

        if not token.is_valid:
            raise InvalidOperationError('This verification link has expired. Please request a new one.')

        token.user.is_email_verified = True
        token.user.save(update_fields=['is_email_verified'])
        token.is_used = True
        token.save(update_fields=['is_used'])
        return token.user

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str):
        """Change login password after verifying the current one."""
        verified = authenticate(username=user.username, password=current_password)
        if not verified:
            raise InvalidOperationError('Current password is incorrect.')
        user.set_password(new_password)
        user.save(update_fields=['password'])

    @staticmethod
    def set_transaction_password(user: User, raw_password: str, confirm_password: str):
        """Set or change the transaction password."""
        if raw_password != confirm_password:
            raise InvalidOperationError('Transaction passwords do not match.')
        if len(raw_password) < 6:
            raise InvalidOperationError('Transaction password must be at least 6 characters.')
        user.set_transaction_password(raw_password)
        user.save(update_fields=['transaction_password'])

    @staticmethod
    def verify_transaction_password(user: User, raw_password: str):
        """
        Raises InvalidTransactionPasswordError if password doesn't match.
        Used by wallet/withdrawal operations.
        """
        if not user.check_transaction_password(raw_password):
            raise InvalidTransactionPasswordError()
