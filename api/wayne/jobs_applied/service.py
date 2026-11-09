from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.dad.job import JobApplied
from api.wayne.jobs_applied.schema import JobAppliedCreate, JobAppliedUpdate


class JobAppliedService:

    @staticmethod
    def create(body: JobAppliedCreate, db: Session) -> JobApplied:
        job = JobApplied(**body.model_dump())
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get(job_id: int, db: Session) -> JobApplied:
        job = db.query(JobApplied).filter(JobApplied.id == job_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    @staticmethod
    def list(db: Session) -> list[JobApplied]:
        return db.query(JobApplied).all()

    @staticmethod
    def update(job_id: int, body: JobAppliedUpdate, db: Session) -> JobApplied:
        job = JobAppliedService.get(job_id, db)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(job, field, value)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete(job_id: int, db: Session) -> None:
        job = JobAppliedService.get(job_id, db)
        db.delete(job)
        db.commit()
