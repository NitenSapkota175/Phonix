"""
Referral Celery tasks — generation income, matching bonus, volume reset.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='apps.referral.tasks.distribute_generation_income', bind=True, max_retries=3)
def distribute_generation_income(self, trade_id: int):
    """
    Triggered after a trade is activated.
    Distributes 20-level generation income to upline chain.
    """
    try:
        from apps.trading.models import Trade
        from .services import ReferralService
        trade = Trade.objects.select_related('user__referred_by').get(pk=trade_id)
        result = ReferralService.distribute_generation_income(trade)
        logger.info('Generation income distributed for trade #%s: %s', trade_id, result)
        return result
    except Exception as exc:
        logger.error('Generation income task failed for trade #%s: %s', trade_id, exc)
        raise self.retry(exc=exc, countdown=30)


@shared_task(name='apps.referral.tasks.calculate_weekly_matching_bonus', bind=True)
def calculate_weekly_matching_bonus(self):
    """Weekly matching bonus — runs Monday 02:00 UTC."""
    from .services import ReferralService
    result = ReferralService.calculate_weekly_matching_bonus()
    logger.info('Weekly matching bonus: %s', result)
    return result


@shared_task(name='apps.referral.tasks.reset_fresh_volumes', bind=True)
def reset_fresh_volumes(self):
    """Reset fresh binary volumes for next week — runs Monday 00:30 UTC."""
    from .services import ReferralService
    result = ReferralService.reset_fresh_volumes()
    logger.info('Fresh volumes reset: %s', result)
    return result
