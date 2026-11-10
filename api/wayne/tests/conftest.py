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
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

# ── 1. Project root on sys.path ───────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── 2. Inline models ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    firstname = Column(String, nullable=False)
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

class JobApplied(Base):
    __tablename__ = "jobs_applied"
    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    job_status = Column(String, default="watch_list", nullable=False)
    location = Column(String, nullable=True)
    job_url = Column(String, nullable=True)
    applied_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Network(Base):
    __tablename__ = "network"
    id = Column(Integer, primary_key=True)
    job_applied_id = Column(Integer, nullable=False, unique=True)
    hiring_manager = Column(String, nullable=True)
    technical_recruiter = Column(String, nullable=True)
    peers = Column(JSON, nullable=True)   # list[str] — JSON stands in for PG ARRAY
    hiring_name = Column(String, nullable=True)
    technical_name = Column(String, nullable=True)
    peer_name = Column(String, nullable=True)

# ── 3. SQLite in-memory engine ────────────────────────────────────────────────
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

# ── 4. Fake settings ──────────────────────────────────────────────────────────
class TestSettings:
    SECRET_KEY = "test-secret-key-must-be-32-chars!"
    LOGIN_SECRET = "test-login-secret"
    DATABASE_URL = "sqlite:///:memory:"
    FRONTEND_URL = "http://localhost:5173"

# ── 5. Inject mocks BEFORE any api.* imports ─────────────────────────────────
_mock_config = types.ModuleType("api.config.config")
_mock_config.Settings = TestSettings
sys.modules["api.config.config"] = _mock_config
sys.modules["api.config"] = types.ModuleType("api.config")

_mock_dad_auth = types.ModuleType("api.dad.auth")
_mock_dad_auth.User = User
_mock_dad_auth.AccessToken = AccessToken
sys.modules["api.dad.auth"] = _mock_dad_auth

_mock_dad_session = types.ModuleType("api.dad.session")
_mock_dad_session.session = _test_session
sys.modules["api.dad.session"] = _mock_dad_session

_mock_dad_job = types.ModuleType("api.dad.job")
_mock_dad_job.JobApplied = JobApplied
_mock_dad_job.Network = Network
sys.modules["api.dad.job"] = _mock_dad_job

# ── 6. Now safe to import app code ───────────────────────────────────────────
from api.daisy.routes import auth_router, limiter as _route_limiter  # noqa: E402
from api.daisy.utils.password_utils import hash_password              # noqa: E402
from api.wayne.routes import wayne_router                             # noqa: E402

_route_limiter.enabled = False

# ── 7. Test app ───────────────────────────────────────────────────────────────
app = FastAPI()
app.state.limiter = Limiter(key_func=get_remote_address)
app.add_middleware(SlowAPIMiddleware)
app.include_router(auth_router)
app.include_router(wayne_router)
app.dependency_overrides[_mock_dad_session.session] = _test_session

# ── 8. Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clean_db():
    db = TestSession()
    db.query(Network).delete()
    db.query(JobApplied).delete()
    db.query(AccessToken).delete()
    db.query(User).delete()
    db.commit()
    db.close()

@pytest.fixture
def test_user(clean_db):
    db = TestSession()
    user = User(
        email="elaine@test.com",
        firstname="Elaine",
        pwd_hash=hash_password("correct-password-123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def auth_headers(client, test_user):
    res = client.post(
        f"/auth/login?key={TestSettings.LOGIN_SECRET}",
        json={"email": "elaine@test.com", "password": "correct-password-123"},
    )
    assert res.status_code == 200, f"auth_headers fixture failed: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def a_job(client, auth_headers):
    res = client.post(
        "/jobs-applied",
        json={"company": "Acme", "job_title": "Software Engineer"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    return res.json()

@pytest.fixture
def a_network(client, auth_headers, a_job):
    res = client.post(
        "/network",
        json={
            "job_applied_id": a_job["id"],
            "hiring_manager": "jane@acme.com",
            "hiring_name": "Jane Smith",
            "technical_recruiter": "bob@acme.com",
            "technical_name": "Bob Lee",
            "peers": ["alice@acme.com"],
            "peer_name": "Alice Wu",
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    return res.json()
