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
from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

# ── 1. Project root on sys.path ───────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── 2. Inline models (mirrors api/dad/auth.py) ──────────────────────────
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

# ── 3. SQLite test database ───────────────────────────────────────────────────
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

# ── 5. Inject mocks into sys.modules BEFORE any api.daisy import ─────────────
_mock_config_config = types.ModuleType("api.config.config")
_mock_config_config.Settings = TestSettings
sys.modules["api.config.config"] = _mock_config_config
sys.modules["api.config"] = types.ModuleType("api.config")

_mock_db_auth = types.ModuleType("api.dad.auth")
_mock_db_auth.User = User
_mock_db_auth.AccessToken = AccessToken
sys.modules["api.dad.auth"] = _mock_db_auth

_mock_db_session = types.ModuleType("api.dad.session")
_mock_db_session.session = _test_session
sys.modules["api.dad.session"] = _mock_db_session
sys.modules["api.dad"] = types.ModuleType("api.dad")

# ── 6. Now safe to import daisy ───────────────────────────────────────────────
from api.daisy.routes import auth_router, limiter as _route_limiter  # noqa: E402
from api.daisy.utils.password_utils import hash_password  # noqa: E402

_route_limiter.enabled = False

# ── 7. Test app ───────────────────────────────────────────────────────────────
app = FastAPI()
app.state.limiter = Limiter(key_func=get_remote_address)
app.add_middleware(SlowAPIMiddleware)
app.include_router(auth_router)
app.dependency_overrides[_mock_db_session.session] = _test_session

# ── 8. Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clean_db():
    db = TestSession()
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
def inactive_user(clean_db):
    db = TestSession()
    user = User(
        email="inactive@test.com",
        firstname="Inactive",
        pwd_hash=hash_password("some-password"),
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.close()

@pytest.fixture
def login_secret():
    return TestSettings.LOGIN_SECRET

@pytest.fixture
def auth_token(client, test_user, login_secret):
    res = client.post(
        f"/auth/login?key={login_secret}",
        json={"email": "elaine@test.com", "password": "correct-password-123"},
    )
    assert res.status_code == 200, f"auth_token fixture failed: {res.text}"
    return res.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
