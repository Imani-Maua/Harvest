import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.dad.enums import HiringRole
from api.dad.job import JobApplied
from api.dad.outreach import OutreachContact
from api.warren.config import Settings

_SEARCH_TITLES = "engineering manager,head of engineering,hiring manager"

log = get_logger(__name__)


def _infer_role(position: str) -> HiringRole:
    p = position.lower()
    if "head of engineering" in p:
        return HiringRole.head_of_engineering
    if "hiring manager" in p:
        return HiringRole.hiring_manager
    return HiringRole.engineering_manager


class HunterService:

    @staticmethod
    def find_contacts(job_id: int, db: Session) -> list[OutreachContact]:
        job = db.query(JobApplied).filter(JobApplied.id == job_id).first()
        if not job:
            log.warning("hunter_job_not_found", extra={"job_id": job_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        settings = Settings()
        if not settings.HUNTER_API_KEY:
            log.error("hunter_api_key_missing", extra={"job_id": job_id})
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="HUNTER_API_KEY is not configured",
            )

        log.info("hunter_domain_search_start", extra={"job_id": job_id, "company": job.company})

        try:
            response = httpx.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "company": job.company,
                    "job_titles": _SEARCH_TITLES,
                    "limit": 10,
                    "api_key": settings.HUNTER_API_KEY,
                },
                timeout=15.0,
            )
        except httpx.RequestError as exc:
            log.error("hunter_request_failed", extra={"job_id": job_id, "company": job.company, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Hunter API request failed")

        if response.status_code == 401:
            log.error("hunter_invalid_api_key", extra={"job_id": job_id})
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hunter API key is invalid",
            )
        response.raise_for_status()

        emails = response.json().get("data", {}).get("emails", [])

        contacts: list[OutreachContact] = []
        new_count = 0
        skipped_count = 0
        for entry in emails:
            existing = (
                db.query(OutreachContact)
                .filter(
                    OutreachContact.job_applied_id == job_id,
                    OutreachContact.email == entry["value"],
                )
                .first()
            )
            if existing:
                skipped_count += 1
                contacts.append(existing)
                continue

            contact = OutreachContact(
                job_applied_id=job_id,
                first_name=entry.get("first_name") or "",
                last_name=entry.get("last_name") or "",
                email=entry["value"],
                position=entry.get("position"),
                hiring_role=_infer_role(entry.get("position") or ""),
                linkedin_url=entry.get("linkedin"),
                confidence=entry.get("confidence"),
                verification_status=entry.get("verification", {}).get("status"),
                source_type=entry.get("source_type"),
                provenance=entry.get("provenance"),
            )
            db.add(contact)
            new_count += 1
            contacts.append(contact)

        try:
            db.commit()
            for c in contacts:
                db.refresh(c)
        except Exception as exc:
            db.rollback()
            log.error("hunter_contacts_save_failed", extra={"job_id": job_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save contacts")

        log.info(
            "hunter_domain_search_complete",
            extra={"job_id": job_id, "company": job.company, "new": new_count, "skipped_duplicates": skipped_count},
        )
        return contacts
