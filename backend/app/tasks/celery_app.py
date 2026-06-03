from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "git_habits",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "backup-database-daily": {
            "task": "backup_database",
            "schedule": crontab(hour=2, minute=0),
        },
    },
    timezone="Asia/Shanghai",
)
