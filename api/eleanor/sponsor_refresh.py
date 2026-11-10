import csv
import io
import json
import logging
import re
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from api.dad.sponsor import SponsorRegister
from api.dad.session import SessionLocal

logger = logging.getLogger(__name__)

UK_REGISTER_PAGE = (
    "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
)


def _log(level: str, event: str, **kwargs) -> str:
    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "logger": "api.eleanor.sponsor_refresh",
        "event": event,
        **kwargs,
    })


def _fetch_uk_names() -> list[str]:
    page = requests.get(UK_REGISTER_PAGE, timeout=15)
    page.raise_for_status()
    csv_urls = re.findall(
        r'https://assets\.publishing\.service\.gov\.uk[^"\']+Worker_and_Temporary_Worker[^"\']*\.csv',
        page.text,
    )
    if not csv_urls:
        return []
    csv_resp = requests.get(csv_urls[0], timeout=30)
    csv_resp.raise_for_status()
    reader = csv.reader(io.StringIO(csv_resp.text))
    names = []
    for i, row in enumerate(reader):
        if i == 0:
            continue
        if row:
            names.append(row[0].strip().lower())
    return names


def refresh_sponsor_register() -> None:
    logger.info(_log("info", "sponsor_refresh_started"))
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        uk_names = _fetch_uk_names()
        if not uk_names:
            logger.warning(_log("warning", "sponsor_refresh_uk_empty"))
        else:
            db.query(SponsorRegister).filter(SponsorRegister.country == "GB").delete()
            db.bulk_save_objects([
                SponsorRegister(company_name=name, country="GB", is_active=True, refreshed_at=now)
                for name in uk_names
            ])
            logger.info(_log("info", "sponsor_refresh_uk_done", count=len(uk_names)))

        db.commit()
        logger.info(_log("info", "sponsor_refresh_complete"))
    except Exception as exc:
        db.rollback()
        logger.error(_log("error", "sponsor_refresh_failed", error=str(exc)))
        raise
    finally:
        db.close()


def get_uk_sponsors(db: Session) -> set[str]:
    rows = (
        db.query(SponsorRegister.company_name)
        .filter(SponsorRegister.country == "GB", SponsorRegister.is_active.is_(True))
        .all()
    )
    return {r.company_name for r in rows}
