"""
Celery tasks for the Earnings app.
Handles daily bond income and generation income distribution.
"""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import logging

from accounts.models import User
from accounts.utils import get_upline_chain
from investment.models import Subscription
from wallet.models import Transaction as WalletTransaction
from .models import Commission, COMMISSION_RATES, DIRECT_REQUIREMENTS

logger = logging.getLogger(__name__)


@shared_task
def calculate_daily_bond_income():
    """
    Calculate and distribute daily bond income for all active subscriptions.
    Runs Monday-Friday only.
    
    Formula: (amount * monthly_rate / 100) / 30 days
    """
    # Check if today is a weekday (Monday=0, Sunday=6)
    today = timezone.now()
    if today.weekday() >= 5:  # Saturday or Sunday
        logger.info("Skipping daily bond income - weekend")
        return {"status": "skipped", "reason": "weekend"}
    
    active_subscriptions = Subscription.objects.filter(is_active=True)
    total_processed = 0
    total_amount = Decimal('0.00')
    
    for subscription in active_subscriptions:
        try:
            with transaction.atomic():
                # Calculate daily income
                daily_income = subscription.calculate_daily_income()
                
                # Check if subscription can still earn
                if not subscription.can_earn(daily_income):
                    # Partial payment if near cap
                    daily_income = subscription.get_remaining_earnings_capacity()
                    if daily_income <= 0:
                        subscription.is_active = False
                        subscription.save()
                        continue
                
                # Check user's 3x earnings cap
                user = subscription.user
                if not user.can_receive_commission(daily_income):
                    # Calculate partial amount user can receive
                    daily_income = user.get_available_commission_amount()
                    if daily_income <= 0:
                        continue
                
                # Add earnings to subscription
                actual_amount = subscription.add_earnings(daily_income)
                
                # Credit user wallet
                user.wallet_balance += actual_amount
                user.total_earnings += actual_amount
                user.save()
                
                # Create commission record
                Commission.objects.create(
                    user=user,
                    from_user=user,
                    level=0,  # 0 for daily bond (own income)
                    amount=actual_amount,
                    commission_type=Commission.DAILY_BOND,
                    source_subscription=subscription,
                    description=f"Daily bond income for {today.date()}"
                )
                
                # Create transaction record
                WalletTransaction.objects.create(
                    user=user,
                    type=WalletTransaction.DAILY_INCOME,
                    amount=actual_amount,
                    fee=Decimal('0.00'),
                    net_amount=actual_amount,
                    status=WalletTransaction.COMPLETED,
                    subscription=subscription,
                    description=f"Daily bond income - {subscription.tier}"
                )
                
                total_processed += 1
                total_amount += actual_amount
                
        except Exception as e:
            logger.error(f"Error processing subscription {subscription.id}: {str(e)}")
            continue
    
    logger.info(f"Daily bond income processed: {total_processed} subscriptions, ${total_amount}")
    return {
        "status": "completed",
        "subscriptions_processed": total_processed,
        "total_amount": str(total_amount)
    }


@shared_task
def distribute_generation_income(subscription_id):
    """
    Distribute generation income (referral commissions) for a new subscription purchase.
    Distributes to 20 levels of upline based on commission rates and direct requirements.
    
    Args:
        subscription_id: ID of the subscription that triggered commissions
    """
    try:
        subscription = Subscription.objects.get(id=subscription_id)
    except Subscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found")
        return {"status": "error", "message": "Subscription not found"}
    
    user = subscription.user
    amount = subscription.amount
    upline_chain = get_upline_chain(user, levels=20)
    
    total_distributed = Decimal('0.00')
    commissions_paid = 0
    
    for level, upline_user in upline_chain:
        try:
            with transaction.atomic():
                # Get commission rate for this level
                commission_rate = COMMISSION_RATES.get(level, Decimal('0.00'))
                if commission_rate == 0:
                    continue
                
                # Check direct referral requirement
                required_directs = DIRECT_REQUIREMENTS.get(level, 0)
                if upline_user.direct_referrals_count < required_directs:
                    logger.info(
                        f"Skipping Level {level} for {upline_user.username}: "
                        f"needs {required_directs} directs, has {upline_user.direct_referrals_count}"
                    )
                    continue
                
                # Calculate commission amount
                commission_amount = amount * commission_rate
                
                # Check 3x earnings cap
                if not upline_user.can_receive_commission(commission_amount):
                    # Calculate partial amount
                    commission_amount = upline_user.get_available_commission_amount()
                    if commission_amount <= 0:
                        logger.info(f"User {upline_user.username} has reached 3x earnings cap")
                        continue
                
                # Credit commission to upline user
                upline_user.wallet_balance += commission_amount
                upline_user.total_earnings += commission_amount
                upline_user.save()
                
                # Create commission record
                Commission.objects.create(
                    user=upline_user,
                    from_user=user,
                    level=level,
                    amount=commission_amount,
                    commission_type=Commission.GENERATION,
                    source_subscription=subscription,
                    description=f"Level {level} commission from {user.username}'s ${amount} subscription"
                )
                
                # Create transaction record
                WalletTransaction.objects.create(
                    user=upline_user,
                    type=WalletTransaction.COMMISSION,
                    amount=commission_amount,
                    fee=Decimal('0.00'),
                    net_amount=commission_amount,
                    status=WalletTransaction.COMPLETED,
                    subscription=subscription,
                    description=f"Level {level} commission from {user.username}"
                )
                
                total_distributed += commission_amount
                commissions_paid += 1
                
        except Exception as e:
            logger.error(f"Error distributing to level {level}: {str(e)}")
            continue
    
    logger.info(
        f"Generation income distributed for subscription {subscription_id}: "
        f"{commissions_paid} commissions, ${total_distributed}"
    )
    
    return {
        "status": "completed",
        "subscription_id": subscription_id,
        "commissions_paid": commissions_paid,
        "total_distributed": str(total_distributed)
    }


@shared_task
def process_subscription_purchase(user_id, amount, bonus_used=Decimal('0.00')):
    """
    Process a subscription purchase including validation and commission distribution.
    
    Args:
        user_id: ID of the user making the purchase
        amount: Subscription amount
        bonus_used: Amount of registration bonus used
    
    Returns:
        dict with status and subscription_id or error message
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"status": "error", "message": "User not found"}
    
    try:
        with transaction.atomic():
            # Validate minimum amount
            if amount < 50:
                return {"status": "error", "message": "Minimum investment is $50"}
            
            # Validate bonus usage (max 10% of purchase)
            max_bonus_allowed = amount * Decimal('0.10')
            if bonus_used > max_bonus_allowed:
                return {
                    "status": "error",
                    "message": f"Bonus usage limited to 10% (${max_bonus_allowed})"
                }
            
            if bonus_used > user.registration_bonus:
                return {
                    "status": "error",
                    "message": "Insufficient registration bonus"
                }
            
            # Calculate wallet amount needed
            wallet_needed = amount - bonus_used
            if wallet_needed > user.wallet_balance:
                return {
                    "status": "error",
                    "message": "Insufficient wallet balance"
                }
            
            # Deduct from user balances
            user.wallet_balance -= wallet_needed
            user.registration_bonus -= bonus_used
            user.total_invested += amount
            user.is_active_investor = True
            user.save()
            
            # Create subscription
            subscription = Subscription.objects.create(
                user=user,
                amount=amount,
                bonus_used=bonus_used
            )
            
            # Create purchase transaction
            WalletTransaction.objects.create(
                user=user,
                type=WalletTransaction.PURCHASE,
                amount=amount,
                fee=Decimal('0.00'),
                net_amount=amount,
                status=WalletTransaction.COMPLETED,
                subscription=subscription,
                description=f"Subscription purchase - {subscription.tier}"
            )
            
            # Trigger generation income distribution
            distribute_generation_income.delay(subscription.id)
            
            return {
                "status": "success",
                "subscription_id": subscription.id,
                "message": "Subscription purchased successfully"
            }
            
    except Exception as e:
        logger.error(f"Error processing subscription purchase: {str(e)}")
        return {"status": "error", "message": str(e)}
