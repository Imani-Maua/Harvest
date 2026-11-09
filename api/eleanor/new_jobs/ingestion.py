from typing import Type

from sqlalchemy.orm import Session

from api.logger import get_logger
from api.dad.job import JobApplied
from api.eleanor.new_jobs.base import JobAdapter, JobAppliedCreate
from api.eleanor.new_jobs.dedup import deduplicate
from api.eleanor.new_jobs.sponsorship import classify_sponsorship, download_uk_sponsors
from api.eleanor.new_jobs.adapters.greenhouse import GreenhouseAdapter
from api.eleanor.new_jobs.adapters.lever import LeverAdapter
from api.eleanor.new_jobs.adapters.ashby import AshbyAdapter
from api.eleanor.new_jobs.adapters.adzuna import AdzunaAdapter
from api.eleanor.new_jobs.adapters.reed import ReedAdapter
from api.eleanor.new_jobs.adapters.jooble import JoobleAdapter

log = get_logger(__name__)

ADAPTERS: list[Type[JobAdapter]] = [
    GreenhouseAdapter,
    LeverAdapter,
    AshbyAdapter,
    AdzunaAdapter,
    ReedAdapter,
    JoobleAdapter,
]


def run_ingestion(db: Session) -> dict:
    log.info("ingestion_started")
    uk_sponsors = download_uk_sponsors()
    log.info("uk_sponsors_loaded", extra={"count": len(uk_sponsors)})

    fetched: list[JobAppliedCreate] = []
    adapter_errors: dict[str, str] = {}

    for adapter_cls in ADAPTERS:
        name = adapter_cls.__name__
        try:
            adapter = adapter_cls()
            jobs = adapter.fetch(db=db)
            log.info("adapter_fetch_complete", extra={"adapter": name, "jobs_fetched": len(jobs)})
            fetched.extend(jobs)
        except Exception as exc:
            log.error("adapter_fetch_failed", extra={"adapter": name, "error": str(exc)})
            adapter_errors[name] = str(exc)

    log.info("ingestion_dedup_start", extra={"total_fetched": len(fetched)})
    new_jobs = deduplicate(fetched, db)
    log.info("ingestion_dedup_complete", extra={"new_jobs": len(new_jobs), "skipped": len(fetched) - len(new_jobs)})

    saved = 0
    for job_data in new_jobs:
        status, evidence = classify_sponsorship(
            job_data.company,
            job_data.description or "",
            uk_sponsors,
        )
        job = JobApplied(
            company=job_data.company,
            job_title=job_data.job_title,
            job_status=job_data.job_status,
            location=job_data.location,
            job_url=job_data.job_url,
            applied_date=job_data.applied_date,
            notes=job_data.notes,
            source=job_data.source,
            posted_date=job_data.posted_date,
            deadline=job_data.deadline,
            description=job_data.description,
            sponsorship_status=status,
            sponsorship_evidence=evidence,
        )
        db.add(job)
        saved += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        log.error("ingestion_commit_failed", extra={"error": str(exc)})
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to save ingested jobs")

    log.info("ingestion_complete", extra={"fetched": len(fetched), "saved": saved, "skipped": len(fetched) - saved, "adapter_errors": len(adapter_errors)})
    return {
        "fetched": len(fetched),
        "new": saved,
        "skipped": len(fetched) - saved,
        "adapter_errors": adapter_errors,
    }
