import json
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from api.dad.session import SessionLocal

logger = logging.getLogger(__name__)


def _log(level: str, event: str, **kwargs) -> str:
    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "logger": "api.warren.scheduler",
        "event": event,
        **kwargs,
    })


def _run_ingestion() -> None:
    from api.eleanor.new_jobs.ingestion import run_ingestion
    db = SessionLocal()
    try:
        logger.info(_log("info", "scheduled_ingestion_started"))
        result = run_ingestion(db)
        logger.info(_log("info", "scheduled_ingestion_complete", **result))
    except Exception as exc:
        logger.error(_log("error", "scheduled_ingestion_failed", error=str(exc)))
    finally:
        db.close()


def _run_sponsor_refresh() -> None:
    from api.eleanor.sponsor_refresh import refresh_sponsor_register
    try:
        logger.info(_log("info", "scheduled_sponsor_refresh_started"))
        refresh_sponsor_register()
        logger.info(_log("info", "scheduled_sponsor_refresh_complete"))
    except Exception as exc:
        logger.error(_log("error", "scheduled_sponsor_refresh_failed", error=str(exc)))


def build_scheduler() -> BackgroundScheduler:
    tz = "Europe/Budapest"
    scheduler = BackgroundScheduler(timezone=tz)

    for hour in (8, 12, 18):
        scheduler.add_job(
            _run_ingestion,
            CronTrigger(hour=hour, minute=0, timezone=tz),
            id=f"ingestion_{hour}h",
            replace_existing=True,
        )

    scheduler.add_job(
        _run_sponsor_refresh,
        CronTrigger(hour=12, minute=0, timezone=tz),
        id="sponsor_refresh",
        replace_existing=True,
    )

    return scheduler
