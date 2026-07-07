"""
scheduler.py
────────────
Sets up APScheduler to run fetch_and_store() every day at 00:00 (midnight).

Place this file inside your  market_finder/  app folder.
It is called once from  apps.py  when Django starts.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)


def start():
    from .data_manager import fetch_and_store

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        fetch_and_store,
        trigger=CronTrigger(hour=0, minute=0),   # every day at midnight IST
        id="daily_mandi_fetch",
        name="Download daily Gujarat mandi prices",
        replace_existing=True,
        misfire_grace_time=3600,                 # if server was down, run within 1 hr
    )

    scheduler.start()
    logger.info("✅ APScheduler started — daily mandi fetch scheduled at midnight IST")
