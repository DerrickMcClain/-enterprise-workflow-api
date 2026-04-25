import logging

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()
log = logging.getLogger(__name__)

celery_app = Celery(
    "enterprise_workflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "overdue-reminder-daily": {
            "task": "app.workers.tasks.overdue_reminder_task",
            "schedule": crontab(hour=8, minute=0),
        },
        "cleanup-refresh-tokens-weekly": {
            "task": "app.workers.tasks.cleanup_expired_refresh_tokens",
            "schedule": crontab(hour=3, minute=0, day_of_week=1),
        },
    },
)
celery_app.autodiscover_tasks(packages=["app.workers"], related_name="tasks")
