"""
Email notification utilities for Phonix MLM platform.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_registration_welcome(user):
    """Send welcome email to newly registered user"""
    subject = 'Welcome to Phonix MLM Platform!'
    message = f"""
Hi {user.username},

Welcome to Phonix! Thank you for joining our platform.

Your account has been successfully created and you've received a $10 registration bonus.

You can use up to 10% of your registration bonus towards your first subscription.

Your unique referral code: {user.referral_code}

Get started by making your first investment at: {settings.SITE_URL}/investment/

If you have any questions, please contact us at {settings.ADMIN_EMAIL}

Best regards,
The Phonix Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending welcome email to {user.email}: {e}")


def send_deposit_confirmation(transaction):
    """Send email confirmation for deposit"""
    user = transaction.user
    subject = 'Deposit Confirmed - Phonix'
    message = f"""
Hi {user.username},

Your deposit of ${transaction.amount} has been successfully confirmed and credited to your wallet.

Transaction Details:
- Amount: ${transaction.amount}
- Transaction Hash: {transaction.txn_hash}
- Status: Completed
- Date: {transaction.completed_at}

Your new wallet balance: ${user.wallet_balance}

Thank you for using Phonix!

Best regards,
The Phonix Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending deposit confirmation to {user.email}: {e}")


def send_withdrawal_processed(transaction):
    """Send email when withdrawal is processed"""
    user = transaction.user
    subject = 'Withdrawal Processed - Phonix'
    message = f"""
Hi {user.username},

Your withdrawal request has been processed.

Withdrawal Details:
- Amount: ${transaction.amount}
- Fee (5%): ${transaction.fee}
- Net Amount: ${transaction.net_amount}
- Destination Address: {transaction.wallet_address}
- Status: Completed
- Date: {transaction.completed_at}

The funds should arrive in your wallet within a few minutes.

Best regards,
The Phonix Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending withdrawal notification to {user.email}: {e}")


def send_rank_advancement(user, rank):
    """Send email notification for rank advancement"""
    subject = f'Congratulations! Rank Advancement to {rank.get_current_rank_display()}'
    message = f"""
Hi {user.username},

Congratulations! You've been promoted to {rank.get_current_rank_display()}!

Rank Details:
- New Rank: {rank.get_current_rank_display()}
- Weekly Bonus: ${rank.weekly_bonus_amount}
- Weeks Remaining: {rank.weeks_remaining}
- Main Leg Volume: ${rank.main_leg_volume}
- Other Legs Volume: ${rank.other_legs_volume}

Keep up the great work building your network!

Best regards,
The Phonix Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending rank advancement email to {user.email}: {e}")


def send_daily_earnings_summary(user, amount):
    """Send daily earnings summary"""
    subject = 'Your Daily Earnings - Phonix'
    message = f"""
Hi {user.username},

You've earned ${amount} in daily bond income today!

Account Summary:
- Today's Earnings: ${amount}
- Total Earnings: ${user.total_earnings}
- Wallet Balance: ${user.wallet_balance}
- Earnings Cap Progress: {user.earnings_cap_percentage:.1f}%

View your full dashboard at: {settings.SITE_URL}/dashboard/

Best regards,
The Phonix Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending daily summary to {user.email}: {e}")
