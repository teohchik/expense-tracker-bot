from celery import Celery
from celery.schedules import crontab

from config import settings

celery_inst = Celery("tasks", broker=settings.redis_url, include=["tasks.tasks"])

# Beat schedule configuration
celery_inst.conf.beat_schedule = {
    "monthly-stats-1st": {
        "task": "monthly_stats",
        "schedule": crontab(day_of_month=1, hour=9, minute=0),  # 1st day of month at 09:00
    },
    "new-month-reminder-daily": {
        "task": "new_month_reminder",
        "schedule": crontab(hour=18, minute=0),  # Every day at 18:00 (checks if last day inside task)
    },
    # TEST TASKS - Uncomment to test functionality
    # "test-monthly-stats": {
    #     "task": "monthly_stats",
    #     "schedule": crontab(minute="*/2"),  # Every 2 minutes for testing
    # },
    # "test-new-month-reminder": {
    #     "task": "new_month_reminder_test",  # Uses forced test version
    #     "schedule": crontab(minute="*/3"),  # Every 3 minutes for testing
    # }
}

celery_inst.conf.timezone = "Europe/Kiev"