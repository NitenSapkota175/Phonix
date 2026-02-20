"""
Ranks Celery tasks — weekly rank evaluation and bonus distribution.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='apps.ranks.tasks.evaluate_all_ranks', bind=True)
def evaluate_all_ranks(self):
    """
    Evaluate all users for rank qualification.
    Runs every Sunday 23:00 UTC.
    """
    from apps.accounts.models import User
    from .services import RankService

    users = User.objects.filter(
        is_active_investor=True
    ).prefetch_related('binary_node')

    evaluated = 0
    newly_ranked = 0

    for user in users:
        result = RankService.evaluate_and_assign(user)
        evaluated += 1
        if result:
            newly_ranked += 1

    logger.info('Rank evaluation: %s users checked, %s newly ranked', evaluated, newly_ranked)
    return {'evaluated': evaluated, 'newly_ranked': newly_ranked}


@shared_task(name='apps.ranks.tasks.pay_weekly_rank_bonuses', bind=True)
def pay_weekly_rank_bonuses(self):
    """
    Pay weekly bonuses to all active ranked users.
    Runs every Monday 01:00 UTC (after evaluation).
    """
    from .services import RankService
    result = RankService.pay_weekly_bonuses()
    logger.info('Weekly rank payouts: %s', result)
    return result
