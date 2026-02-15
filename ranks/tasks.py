"""
Celery tasks for the Ranks app.
Handles rank advancement checks and weekly bonus distribution.
"""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from accounts.models import User
from accounts.utils import count_leg_volumes
from wallet.models import Transaction as WalletTransaction
from .models import Rank

logger = logging.getLogger(__name__)


@shared_task
def check_rank_advancements():
    """
    Check all users for rank advancement based on leg volumes.
    Should run weekly (e.g., every Sunday).
    """
    users_checked = 0
    users_advanced = 0
    
    # Get all users with at least one direct referral
    users = User.objects.filter(direct_referrals_count__gt=0)
    
    for user in users:
        try:
            with transaction.atomic():
                # Get or create rank record
                rank, created = Rank.objects.get_or_create(user=user)
                
                # Calculate leg volumes
                leg_data = count_leg_volumes(user)
                main_leg = leg_data['main_leg_volume']
                other_legs = leg_data['other_legs_volume']
                
                # Update volumes
                rank.update_volumes(main_leg, other_legs)
                
                # Check for rank advancement
                new_rank = rank.check_rank_advancement()
                
                if new_rank:
                    users_advanced += 1
                    logger.info(
                        f"User {user.username} advanced to {new_rank}: "
                        f"Main Leg ${main_leg}, Other Legs ${other_legs}"
                    )
                
                users_checked += 1
                
        except Exception as e:
            logger.error(f"Error checking rank for user {user.id}: {str(e)}")
            continue
    
    logger.info(f"Rank advancement check: {users_checked} users checked, {users_advanced} advanced")
    
    return {
        "status": "completed",
        "users_checked": users_checked,
        "users_advanced": users_advanced
    }


@shared_task
def distribute_weekly_bonuses():
    """
    Distribute weekly bonuses to users with active ranks.
    Should run weekly (e.g., every Monday).
    """
    ranks_with_bonus = Rank.objects.filter(
        weeks_remaining__gt=0,
        weekly_bonus_amount__gt=0
    )
    
    total_distributed = Decimal('0.00')
    bonuses_paid = 0
    
    for rank in ranks_with_bonus:
        try:
            with transaction.atomic():
                user = rank.user
                bonus_amount = rank.weekly_bonus_amount
                
                # Check 3x earnings cap
                if not user.can_receive_commission(bonus_amount):
                    # Calculate partial amount
                    bonus_amount = user.get_available_commission_amount()
                    if bonus_amount <= 0:
                        logger.info(f"User {user.username} has reached 3x earnings cap")
                        continue
                
                # Credit bonus to user wallet
                user.wallet_balance += bonus_amount
                user.total_earnings += bonus_amount
                user.save()
                
                # Decrement weeks remaining
                rank.weeks_remaining -= 1
                rank.save()
                
                # Create transaction record
                WalletTransaction.objects.create(
                    user=user,
                    type=WalletTransaction.WEEKLY_BONUS,
                    amount=bonus_amount,
                    fee=Decimal('0.00'),
                    net_amount=bonus_amount,
                    status=WalletTransaction.COMPLETED,
                    description=f"Weekly {rank.get_current_rank_display()} bonus ({rank.weeks_remaining} weeks remaining)"
                )
                
                total_distributed += bonus_amount
                bonuses_paid += 1
                
        except Exception as e:
            logger.error(f"Error distributing weekly bonus for rank {rank.id}: {str(e)}")
            continue
    
    logger.info(f"Weekly bonuses distributed: {bonuses_paid} bonuses, ${total_distributed}")
    
    return {
        "status": "completed",
        "bonuses_paid": bonuses_paid,
        "total_distributed": str(total_distributed)
    }


@shared_task
def update_all_leg_volumes():
    """
    Update leg volumes for all users.
    This can be resource-intensive, so run during off-peak hours.
    """
    users_updated = 0
    
    users = User.objects.filter(direct_referrals_count__gt=0)
    
    for user in users:
        try:
            rank, created = Rank.objects.get_or_create(user=user)
            
            leg_data = count_leg_volumes(user)
            rank.update_volumes(
                leg_data['main_leg_volume'],
                leg_data['other_legs_volume']
            )
            
            users_updated += 1
            
        except Exception as e:
            logger.error(f"Error updating leg volumes for user {user.id}: {str(e)}")
            continue
    
    logger.info(f"Leg volumes updated for {users_updated} users")
    
    return {
        "status": "completed",
        "users_updated": users_updated
    }
