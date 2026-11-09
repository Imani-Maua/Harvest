from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from api.dad.enums import JobStatus


class JobAppliedCreate(BaseModel):
    company: str
    job_title: str
    job_status: JobStatus = JobStatus.watch_list
    location: Optional[str] = None
    job_url: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None


class JobAppliedUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    job_status: Optional[JobStatus] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None


class JobAppliedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    job_title: str
    job_status: JobStatus
    location: Optional[str]
    job_url: Optional[str]
    applied_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
