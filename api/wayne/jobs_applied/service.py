from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.logger import get_logger
from api.dad.job import JobApplied
from api.wayne.jobs_applied.schema import JobAppliedCreate, JobAppliedUpdate

log = get_logger(__name__)


class JobAppliedService:

    @staticmethod
    def create(body: JobAppliedCreate, db: Session) -> JobApplied:
        try:
            job = JobApplied(**body.model_dump())
            db.add(job)
            db.commit()
            db.refresh(job)
        except Exception as exc:
            db.rollback()
            log.error("job_create_failed", extra={"company": body.company, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save job application")
        log.info("job_created", extra={"job_id": job.id, "company": job.company})
        return job

    @staticmethod
    def get(job_id: int, db: Session) -> JobApplied:
        job = db.query(JobApplied).filter(JobApplied.id == job_id).first()
        if not job:
            log.warning("job_not_found", extra={"job_id": job_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    @staticmethod
    def list(db: Session) -> list[JobApplied]:
        return db.query(JobApplied).all()

    @staticmethod
    def update(job_id: int, body: JobAppliedUpdate, db: Session) -> JobApplied:
        from api.dad.enums import JobStatus
        job = JobAppliedService.get(job_id, db)
        previous_status = job.job_status
        try:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(job, field, value)
            db.commit()
            db.refresh(job)
        except Exception as exc:
            db.rollback()
            log.error("job_update_failed", extra={"job_id": job_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job application")
        log.info("job_updated", extra={"job_id": job_id})

        if previous_status != JobStatus.applied and job.job_status == JobStatus.applied:
            from api.waweru.trigger import on_job_applied
            on_job_applied(job_id=job_id, db=db)

        return job

    @staticmethod
    def delete(job_id: int, db: Session) -> None:
        job = JobAppliedService.get(job_id, db)
        try:
            db.delete(job)
            db.commit()
        except Exception as exc:
            db.rollback()
            log.error("job_delete_failed", extra={"job_id": job_id, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete job application")
        log.info("job_deleted", extra={"job_id": job_id})
