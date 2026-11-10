import importlib.util
import os
import sys
import types
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import (
    Boolean, Column, DateTime, Date, Integer, JSON, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

# ── 1. Project root on sys.path ──────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── 2. Load real enums (pure Python, no DB dependency) ──────────────────────
_espec = importlib.util.spec_from_file_location(
    "api.dad.enums", os.path.join(ROOT, "api", "dad", "enums.py")
)
_emod = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(_emod)
sys.modules["api.dad.enums"] = _emod


# ── 3. SQLite-compatible test models ─────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=True)
    pwd_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AccessToken(Base):
    __tablename__ = "access_tokens"
    id = Column(Integer, primary_key=True)
    token_hash = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    jti = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    headline = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    work_authorisation = Column(String, nullable=True)
    source = Column(String, default="manual", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkExperience(Base):
    __tablename__ = "work_experiences"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    achievements = Column(JSON, nullable=True)
    technologies = Column(JSON, nullable=True)
    source = Column(String, default="manual", nullable=False)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    repo_url = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    technologies = Column(JSON, nullable=True)
    highlights = Column(JSON, nullable=True)
    source = Column(String, default="manual", nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, default="other", nullable=False)
    proficiency = Column(String, nullable=True)
    years_experience = Column(Integer, nullable=True)
    source = Column(String, default="manual", nullable=False)


class CareerPreference(Base):
    __tablename__ = "career_preferences"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    desired_titles = Column(JSON, nullable=True)
    desired_industries = Column(JSON, nullable=True)
    desired_locations = Column(JSON, nullable=True)
    remote_preference = Column(String, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String, default="GBP", nullable=False)
    open_to_contract = Column(Boolean, default=False, nullable=False)
    open_to_parttime = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SupportingLink(Base):
    __tablename__ = "supporting_links"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    link_type = Column(String, default="other", nullable=False)
    label = Column(String, nullable=True)
    url = Column(String, nullable=False)
    source = Column(String, default="manual", nullable=False)


# ── 4. Test database ──────────────────────────────────────────────────────────
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _test_session():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# ── 5. Fake settings ──────────────────────────────────────────────────────────
class TestSettings:
    SECRET_KEY = "test-secret-key-must-be-32-chars!"
    LOGIN_SECRET = "test-login-secret"
    DATABASE_URL = "sqlite:///:memory:"
    FRONTEND_URL = "http://localhost:5173"


# ── 6. Inject mocks into sys.modules BEFORE any api.* import ─────────────────
_mock_config = types.ModuleType("api.config.config")
_mock_config.Settings = TestSettings
sys.modules["api.config.config"] = _mock_config
sys.modules["api.config"] = types.ModuleType("api.config")

_mock_auth = types.ModuleType("api.dad.auth")
_mock_auth.User = User
_mock_auth.AccessToken = AccessToken
sys.modules["api.dad.auth"] = _mock_auth

_mock_session = types.ModuleType("api.dad.session")
_mock_session.session = _test_session
sys.modules["api.dad.session"] = _mock_session

_mock_candidate = types.ModuleType("api.dad.candidate")
_mock_candidate.Candidate = Candidate
_mock_candidate.WorkExperience = WorkExperience
_mock_candidate.Project = Project
_mock_candidate.Skill = Skill
_mock_candidate.CareerPreference = CareerPreference
_mock_candidate.SupportingLink = SupportingLink
sys.modules["api.dad.candidate"] = _mock_candidate

sys.modules["api.dad"] = types.ModuleType("api.dad")


# ── 7. Now safe to import routes ──────────────────────────────────────────────
from api.daisy.routes import auth_router, limiter as _limiter  # noqa: E402
from api.daisy.utils.password_utils import hash_password  # noqa: E402
from api.elaine.internal.routes import (  # noqa: E402
    candidate_router,
    work_experience_router,
    project_router,
    skill_router,
    career_preference_router,
    supporting_link_router,
)

_limiter.enabled = False

# ── 8. Test app ───────────────────────────────────────────────────────────────
app = FastAPI()
app.state.limiter = Limiter(key_func=get_remote_address)
app.add_middleware(SlowAPIMiddleware)
for router in [
    auth_router,
    candidate_router,
    work_experience_router,
    project_router,
    skill_router,
    career_preference_router,
    supporting_link_router,
]:
    app.include_router(router)
app.dependency_overrides[_mock_session.session] = _test_session


# ── 9. Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db():
    db = TestSession()
    for model in [SupportingLink, CareerPreference, Skill, Project, WorkExperience, Candidate, AccessToken, User]:
        db.query(model).delete()
    db.commit()
    db.close()


@pytest.fixture
def test_user(clean_db):
    db = TestSession()
    user = User(
        email="elaine@test.com",
        firstname="Elaine",
        lastname="Maua",
        pwd_hash=hash_password("correct-password-123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def auth_token(client, test_user):
    res = client.post(
        f"/auth/login?key={TestSettings.LOGIN_SECRET}",
        json={"email": "elaine@test.com", "password": "correct-password-123"},
    )
    assert res.status_code == 200, f"auth_token fixture failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def candidate(client, auth_headers):
    res = client.post(
        "/candidates",
        json={
            "firstname": "Elaine",
            "lastname": "Maua",
            "email": "candidate@test.com",
            "headline": "Senior Software Engineer",
        },
        headers=auth_headers,
    )
    assert res.status_code == 201, f"candidate fixture failed: {res.text}"
    return res.json()
