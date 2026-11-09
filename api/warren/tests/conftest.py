import os
import sys
import types
from datetime import datetime

import pytest
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── 1. Inline models (SQLite-compatible) ──────────────────────────────────────
class Base(DeclarativeBase):
    pass


class JobApplied(Base):
    __tablename__ = "jobs_applied"
    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    job_status = Column(String, default="watch_list", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OutreachContact(Base):
    __tablename__ = "outreach_contacts"
    id = Column(Integer, primary_key=True)
    job_applied_id = Column(Integer, ForeignKey("jobs_applied.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    position = Column(String, nullable=True)
    hiring_role = Column(String, nullable=False)
    linkedin_url = Column(String, nullable=True)
    confidence = Column(Integer, nullable=True)
    verification_status = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    provenance = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── 2. SQLite engine ───────────────────────────────────────────────────────────
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── 3. Inject mocks BEFORE any api.* imports ──────────────────────────────────
_mock_dad_job = types.ModuleType("api.dad.job")
_mock_dad_job.JobApplied = JobApplied
sys.modules["api.dad.job"] = _mock_dad_job

_mock_dad_outreach = types.ModuleType("api.dad.outreach")
_mock_dad_outreach.OutreachContact = OutreachContact
sys.modules["api.dad.outreach"] = _mock_dad_outreach


# ── 4. Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_db():
    session = TestSession()
    session.query(OutreachContact).delete()
    session.query(JobApplied).delete()
    session.commit()
    session.close()
    yield


@pytest.fixture
def a_job(db, clean_db):
    job = JobApplied(company="Acme Corp", job_title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
