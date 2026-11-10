from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List

from pydantic import BaseModel

from api.dad.enums import JobStatus


class JobAppliedCreate(BaseModel):
    company: str
    job_title: str
    job_status: JobStatus = JobStatus.watch_list
    location: Optional[str] = None
    job_url: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    posted_date: Optional[date] = None
    deadline: Optional[date] = None
    description: Optional[str] = None


INCLUDE_KEYWORDS = [
    "junior", "graduate", "grad", "new grad", "entry", "entry-level",
    "associate", "software engineer", "backend engineer", "fullstack",
    "full stack", "frontend engineer", "python developer", "software developer",
]

EXCLUDE_KEYWORDS = [
    "senior", "sr.", "lead", "principal", "staff engineer", "manager",
    "director", "head of", "vp", "vice president", "architect",
]

EXCLUDE_EXPERIENCE = [
    "5+ years", "5 years experience", "7+ years", "10+ years", "minimum 5",
]


def passes_title_filter(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_KEYWORDS):
        return False
    return any(kw in t for kw in INCLUDE_KEYWORDS)


def passes_description_filter(description: str) -> bool:
    if not description:
        return True
    d = description.lower()
    return not any(kw in d for kw in EXCLUDE_EXPERIENCE)


def passes_date_filter(posted_date: Optional[date]) -> bool:
    if not posted_date:
        return True
    from datetime import date as date_today
    return (date_today.today() - posted_date).days <= 21


def passes_deadline_filter(deadline: Optional[date]) -> bool:
    if not deadline:
        return True
    from datetime import date as date_today
    return deadline >= date_today.today()


class JobAdapter(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> List[JobAppliedCreate]:
        pass
