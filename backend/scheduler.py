from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.core.logger import LOG
from backend.tasks.cleanup import scan_cleanup_candidates

scheduler = AsyncIOScheduler()


async def test_job():
    print("THIS IS FIRED OFF ASYNC ETC")


def setup_scheduler():
    """Configure and add scheduled tasks."""

    # scheduler.add_job(
    #     test_job,
    #     IntervalTrigger(minutes=1),
    #     id="test_job",
    #     name="Test Job that runs every minute",
    #     replace_existing=True,
    # )

    # # scan for cleanup candidates daily at 2 AM
    # scheduler.add_job(
    #     scan_cleanup_candidates,
    #     CronTrigger(hour=2, minute=0),
    #     id="scan_cleanup_candidates",
    #     name="Scan for cleanup candidates",
    #     replace_existing=True,
    # )

    # # sync watch history every 6 hours
    # scheduler.add_job(
    #     sync_watch_history,
    #     IntervalTrigger(hours=6),
    #     id="sync_watch_history",
    #     name="Sync watch history from media servers",
    #     replace_existing=True,
    # )

    LOG.info("Scheduler configured with tasks")


def start_scheduler():
    """Start the scheduler."""
    setup_scheduler()
    scheduler.start()
    LOG.info("Scheduler started")


async def shutdown_scheduler():
    """Gracefully shutdown the scheduler."""
    scheduler.shutdown(wait=False)
    LOG.info("Scheduler stopped")


# async def trigger_sync_now():
#     """Manually trigger watch history sync (bypasses schedule)."""
#     LOG.info("Manually triggering watch history sync")
#     await sync_watch_history()


async def trigger_cleanup_scan_now():
    """Manually trigger cleanup candidates scan (bypasses schedule)."""
    LOG.info("Manually triggering cleanup candidates scan")
    await scan_cleanup_candidates()
