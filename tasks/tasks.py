import asyncio
from datetime import date

from tasks.celery_app import celery_inst


@celery_inst.task(name="test")
def daily_stats_celery():
    """Test task that runs every minute."""
    print("🔔 Celery Beat Test Task is working!")
    return "Test task completed"


@celery_inst.task(name="monthly_stats")
def monthly_stats_celery():
    """Monthly statistics task that runs on 1st day of month."""
    today = date.today()
    
    if today.day == 1:
        print(f"📊 Monthly stats task executed on {today}")
        # Here you can add logic to send stats
        # Example: asyncio.run(send_monthly_stats())
    
    return f"Monthly stats checked for {today}"


async def send_monthly_stats():
    """Async function to send monthly stats to users."""
    # Example: use api_client to get stats and send to users
    print("Sending monthly stats to users...")
    # Add your async logic here
    pass


# Helper to run async functions from Celery
def run_async(coroutine):
    """Helper to run async coroutines from sync Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()
