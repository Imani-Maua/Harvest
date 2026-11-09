import difflib
from typing import List

from sqlalchemy.orm import Session

from api.dad.job import JobApplied
from api.eleanor.new_jobs.base import JobAppliedCreate


def _url_key(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/").lower().split("?")[0]


def _similar(a: str, b: str, threshold: float = 0.88) -> bool:
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold


def deduplicate(new_jobs: List[JobAppliedCreate], db: Session) -> List[JobAppliedCreate]:
    existing = db.query(JobApplied.job_url, JobApplied.company, JobApplied.job_title).all()

    existing_urls = {_url_key(row.job_url) for row in existing if row.job_url}
    existing_pairs = [
        (row.company.lower().strip(), row.job_title.lower().strip()) for row in existing
    ]

    seen_urls: set[str] = set()
    seen_pairs: list[tuple[str, str]] = []
    result: List[JobAppliedCreate] = []

    for job in new_jobs:
        url_key = _url_key(job.job_url)
        company = job.company.lower().strip()
        title = job.job_title.lower().strip()

        if url_key and url_key in existing_urls:
            continue
        if url_key and url_key in seen_urls:
            continue

        already = False
        for ec, et in existing_pairs + seen_pairs:
            if _similar(company, ec) and _similar(title, et):
                already = True
                break
        if already:
            continue

        if url_key:
            seen_urls.add(url_key)
        seen_pairs.append((company, title))
        result.append(job)

    return result
