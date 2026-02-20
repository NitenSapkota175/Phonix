"""
Trading Celery tasks — daily ROI distribution.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='apps.trading.tasks.calculate_daily_roi', bind=True, max_retries=3)
def calculate_daily_roi(self):
    """
    Distribute daily ROI to all active trade packages.
    Runs Monday–Friday at 00:00 UTC via Celery Beat.
    """
    try:
        from .services import TradeService
        result = TradeService.process_daily_roi()
        logger.info(
            'Daily ROI distributed: processed=%s skipped=%s total=$%s',
            result.get('processed', 0),
            result.get('skipped', 0),
            result.get('total_roi_distributed', '0'),
        )
        return result
    except Exception as exc:
        logger.error('Daily ROI task failed: %s', exc)
        raise self.retry(exc=exc, countdown=60)
