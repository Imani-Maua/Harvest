import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.dad.enums import HiringRole
from api.dad.job import JobApplied
from api.dad.outreach import OutreachContact
from api.warren.config import Settings

_SEARCH_TITLES = "engineering manager,head of engineering,hiring manager"


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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        settings = Settings()
        if not settings.HUNTER_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="HUNTER_API_KEY is not configured",
            )

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

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hunter API key is invalid",
            )
        response.raise_for_status()

        emails = response.json().get("data", {}).get("emails", [])

        contacts: list[OutreachContact] = []
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
            contacts.append(contact)

        db.commit()
        for c in contacts:
            db.refresh(c)

        return contacts
