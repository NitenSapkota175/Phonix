"""
Phonix config package — exposes Celery app for 'celery -A config worker'.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
