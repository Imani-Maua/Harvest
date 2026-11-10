from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dad.auth import User
from api.dad.session import session
from api.daisy.utils.auth_utils import get_current_user
from api.wayne.jobs_applied.schema import JobAppliedCreate, JobAppliedOut, JobAppliedUpdate
from api.wayne.jobs_applied.service import JobAppliedService

jobs_applied_router = APIRouter(prefix="/jobs-applied", tags=["Jobs Applied"])


@jobs_applied_router.post("", response_model=JobAppliedOut, status_code=status.HTTP_201_CREATED)
def create_job(
    body: JobAppliedCreate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return JobAppliedService.create(body=body, db=db)


@jobs_applied_router.get("", response_model=list[JobAppliedOut])
def list_jobs(
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return JobAppliedService.list(db=db)


@jobs_applied_router.get("/{job_id}", response_model=JobAppliedOut)
def get_job(
    job_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return JobAppliedService.get(job_id=job_id, db=db)


@jobs_applied_router.patch("/{job_id}", response_model=JobAppliedOut)
def update_job(
    job_id: int,
    body: JobAppliedUpdate,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return JobAppliedService.update(job_id=job_id, body=body, db=db)


@jobs_applied_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Annotated[Session, Depends(session)],
    _: Annotated[User, Depends(get_current_user)],
):
    JobAppliedService.delete(job_id=job_id, db=db)
