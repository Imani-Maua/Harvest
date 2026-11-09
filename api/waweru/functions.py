import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api.dad.job import JobApplied
from api.dad.enums import JobStatus

logger = logging.getLogger(__name__)


def _log(level: str, event: str, **kwargs) -> str:
    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "logger": "api.waweru.functions",
        "event": event,
        **kwargs,
    })


FUNCTION_DECLARATIONS = [
    {
        "name": "add_to_watchlist",
        "description": "Add a job to Elaine's watch list given a job URL, company name, and job title.",
        "parameters": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Company name"},
                "job_title": {"type": "string", "description": "Job title"},
                "job_url": {"type": "string", "description": "URL of the job posting"},
                "location": {"type": "string", "description": "Job location (optional)"},
            },
            "required": ["company", "job_title", "job_url"],
        },
    },
    {
        "name": "get_watchlist",
        "description": "Get Elaine's current job watch list.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "find_contacts_and_draft_email",
        "description": "Find hiring contacts at a company Elaine has applied to and draft an outreach email.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "ID of the job in Elaine's watch list"},
            },
            "required": ["job_id"],
        },
    },
]


def add_to_watchlist(company: str, job_title: str, job_url: str, db: Session, location: str = "") -> dict:
    logger.info(_log("info", "fn_add_to_watchlist", company=company, job_title=job_title))
    existing = db.query(JobApplied).filter(JobApplied.job_url == job_url).first()
    if existing:
        return {"status": "already_exists", "job_id": existing.id, "message": f"{job_title} at {company} is already in your list."}

    job = JobApplied(
        company=company,
        job_title=job_title,
        job_url=job_url,
        location=location or None,
        job_status=JobStatus.watch_list,
        source="harvest_chat",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(_log("info", "fn_add_to_watchlist_done", job_id=job.id))
    return {"status": "added", "job_id": job.id, "message": f"Added {job_title} at {company} to your watch list."}


def get_watchlist(db: Session) -> dict:
    jobs = db.query(JobApplied).filter(
        JobApplied.job_status == JobStatus.watch_list
    ).order_by(JobApplied.created_at.desc()).limit(20).all()
    return {
        "jobs": [
            {"id": j.id, "company": j.company, "job_title": j.job_title, "location": j.location, "job_url": j.job_url}
            for j in jobs
        ]
    }


def find_contacts_and_draft_email(job_id: int, db: Session) -> dict:
    from api.warren.hunter.service import HunterService
    from api.warren.gmail.service import GmailService
    from api.waweru.outreach import draft_outreach_email

    logger.info(_log("info", "fn_find_contacts_started", job_id=job_id))

    job = db.query(JobApplied).filter(JobApplied.id == job_id).first()
    if not job:
        return {"status": "error", "message": f"No job found with ID {job_id}."}

    contacts = HunterService.find_contacts(job_id=job_id, db=db)
    if not contacts:
        logger.info(_log("info", "fn_find_contacts_none_found", job_id=job_id))
        return {"status": "no_contacts", "message": f"Couldn't find any contacts at {job.company} via Hunter."}

    primary = contacts[0]
    subject, body = draft_outreach_email(job=job, contact=primary)
    draft_id = GmailService.create_draft(
        to_email=primary.email,
        subject=subject,
        body=body,
    )
    logger.info(_log("info", "fn_draft_created", job_id=job_id, draft_id=draft_id, contact_email=primary.email))
    return {
        "status": "draft_created",
        "draft_id": draft_id,
        "contact": f"{primary.first_name} {primary.last_name}",
        "email": primary.email,
        "message": f"Found {primary.first_name} {primary.last_name} at {job.company} and created a Gmail draft.",
    }
