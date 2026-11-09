from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dad.session import session
from api.dad.auth import User
from api.daisy.utils.auth_utils import get_current_user
from api.eleanor.new_jobs.ingestion import run_ingestion

eleanor_router = APIRouter(prefix="/eleanor", tags=["eleanor"])


@eleanor_router.post("/jobs/ingest")
def ingest_jobs(
    db: Session = Depends(session),
    _: User = Depends(get_current_user),
):
    result = run_ingestion(db)
    return result
