from celery import Celery
from celery.schedules import crontab

from config import settings

celery_inst = Celery("tasks", broker=settings.redis_url, include=["tasks.tasks"])

# Beat schedule configuration
celery_inst.conf.beat_schedule = {
    "test-every-minute": {
        "task": "test",
        "schedule": crontab(minute="*/1"),  # Every minute for testing
    },
    "monthly-stats": {
        "task": "monthly_stats",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),  # 1st day of month at 00:00
    }
}

celery_inst.conf.timezone = "UTC"