import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _log(level: str, event: str, **kwargs) -> str:
    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "logger": "api.waweru.trigger",
        "event": event,
        **kwargs,
    })


def on_job_applied(job_id: int, db: Session) -> None:
    from api.waweru.functions import find_contacts_and_draft_email
    logger.info(_log("info", "apply_trigger_fired", job_id=job_id))
    try:
        result = find_contacts_and_draft_email(job_id=job_id, db=db)
        logger.info(_log("info", "apply_trigger_complete", job_id=job_id, result=result))
    except Exception as exc:
        logger.error(_log("error", "apply_trigger_failed", job_id=job_id, error=str(exc)))
