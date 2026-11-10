import os
import sys
import types
from unittest.mock import MagicMock

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestSettings:
    DATABASE_URL = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key-must-be-32-chars!"
    LOGIN_SECRET = "test-login-secret"
    ADZUNA_APP_ID = ""
    ADZUNA_APP_KEY = ""
    REED_API_KEY = ""
    JOOBLE_API_KEY = ""
    GEMINI_API_KEY = ""
    GITHUB_PAT = ""


# Inject before any api.warren or adapter import triggers Settings()
_warren_config_mod = types.ModuleType("api.warren.config")
_warren_config_mod.Settings = TestSettings
sys.modules["api.warren.config"] = _warren_config_mod

_warren_mod = types.ModuleType("api.warren")
sys.modules["api.warren"] = _warren_mod


@pytest.fixture
def mock_db():
    """SQLAlchemy Session mock with an empty existing-jobs result."""
    db = MagicMock()
    db.query.return_value.all.return_value = []
    return db
