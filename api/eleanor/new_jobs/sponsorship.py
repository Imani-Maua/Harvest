import csv
import difflib
import io
import re

import requests
from sqlalchemy.orm import Session

from api.dad.enums import SponsorshipStatus

UK_REGISTER_PAGE = (
    "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
)

NO_SPONSORSHIP_PHRASES = [
    "no visa sponsorship",
    "unable to sponsor",
    "cannot sponsor",
    "not able to sponsor",
    "sponsorship is not available",
    "we do not sponsor",
    "does not offer sponsorship",
    "not currently able to sponsor",
]

YES_SPONSORSHIP_PHRASES = [
    "visa sponsorship provided",
    "we can sponsor",
    "sponsorship available",
    "skilled worker visa",
    "we will sponsor",
    "happy to sponsor",
]


def _fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold


def download_uk_sponsors() -> set[str]:
    try:
        page = requests.get(UK_REGISTER_PAGE, timeout=15)
        page.raise_for_status()
        csv_urls = re.findall(
            r'https://assets\.publishing\.service\.gov\.uk[^"\']+Worker_and_Temporary_Worker[^"\']*\.csv',
            page.text,
        )
        if not csv_urls:
            return set()
        csv_resp = requests.get(csv_urls[0], timeout=30)
        csv_resp.raise_for_status()
        reader = csv.reader(io.StringIO(csv_resp.text))
        sponsors = set()
        for i, row in enumerate(reader):
            if i == 0:
                continue
            if row:
                sponsors.add(row[0].strip().lower())
        return sponsors
    except Exception:
        return set()


def get_uk_sponsors(db: Session) -> set[str]:
    from api.eleanor.sponsor_refresh import get_uk_sponsors as _from_db
    cached = _from_db(db)
    if cached:
        return cached
    return download_uk_sponsors()


def classify_sponsorship(
    company: str, description: str, uk_sponsors: set[str]
) -> tuple[SponsorshipStatus, str]:
    company_normalized = company.lower().strip()
    desc_lower = (description or "").lower()

    for sponsor in uk_sponsors:
        if _fuzzy_match(company_normalized, sponsor):
            return SponsorshipStatus.confirmed, f"Found in UK sponsor register: {sponsor}"

    for phrase in NO_SPONSORSHIP_PHRASES:
        if phrase in desc_lower:
            return SponsorshipStatus.explicitly_unavailable, f'Description states: "{phrase}"'

    for phrase in YES_SPONSORSHIP_PHRASES:
        if phrase in desc_lower:
            return SponsorshipStatus.possible, f'Description mentions: "{phrase}"'

    if "sponsorship" in desc_lower:
        return SponsorshipStatus.requires_clarification, "Sponsorship mentioned in description — needs review"

    return SponsorshipStatus.no_info, "Not in UK sponsor register; no sponsorship mention in description"
