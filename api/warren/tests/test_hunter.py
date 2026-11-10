from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.dad.enums import HiringRole
from api.warren.hunter.service import HunterService, _infer_role


class _Settings:
    HUNTER_API_KEY = "test-api-key"


def _mock_response(status_code=200, emails=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = {"data": {"emails": emails or []}}
    mock.raise_for_status.return_value = None
    return mock


# ── _infer_role ───────────────────────────────────────────────────────────────

def test_infer_role_engineering_manager():
    assert _infer_role("Engineering Manager") == HiringRole.engineering_manager


def test_infer_role_software_engineering_manager():
    assert _infer_role("Software Engineering Manager") == HiringRole.engineering_manager


def test_infer_role_head_of_engineering():
    assert _infer_role("Head of Engineering") == HiringRole.head_of_engineering


def test_infer_role_hiring_manager():
    assert _infer_role("Hiring Manager") == HiringRole.hiring_manager


def test_infer_role_empty_string():
    assert _infer_role("") == HiringRole.engineering_manager


def test_infer_role_case_insensitive():
    assert _infer_role("HEAD OF ENGINEERING") == HiringRole.head_of_engineering


# ── HunterService.find_contacts ───────────────────────────────────────────────

def test_find_contacts_404_job_not_found(db):
    with pytest.raises(HTTPException) as exc:
        HunterService.find_contacts(9999, db)
    assert exc.value.status_code == 404


def test_find_contacts_503_no_api_key(db, a_job):
    class _NoKey:
        HUNTER_API_KEY = ""

    with patch("api.warren.hunter.service.Settings", return_value=_NoKey()):
        with pytest.raises(HTTPException) as exc:
            HunterService.find_contacts(a_job.id, db)
    assert exc.value.status_code == 503


def test_find_contacts_503_invalid_api_key(db, a_job):
    with patch("api.warren.hunter.service.Settings", return_value=_Settings()), \
         patch("api.warren.hunter.service.httpx.get", return_value=_mock_response(401)):
        with pytest.raises(HTTPException) as exc:
            HunterService.find_contacts(a_job.id, db)
    assert exc.value.status_code == 503


def test_find_contacts_returns_contacts(db, a_job):
    emails = [
        {
            "value": "john@acme.com",
            "first_name": "John",
            "last_name": "Doe",
            "position": "Engineering Manager",
            "linkedin": "https://linkedin.com/in/johndoe",
            "confidence": 90,
            "verification": {"status": "valid"},
        }
    ]
    with patch("api.warren.hunter.service.Settings", return_value=_Settings()), \
         patch("api.warren.hunter.service.httpx.get", return_value=_mock_response(emails=emails)):
        contacts = HunterService.find_contacts(a_job.id, db)

    assert len(contacts) == 1
    c = contacts[0]
    assert c.email == "john@acme.com"
    assert c.first_name == "John"
    assert c.last_name == "Doe"
    assert c.position == "Engineering Manager"
    assert c.hiring_role == HiringRole.engineering_manager
    assert c.confidence == 90
    assert c.linkedin_url == "https://linkedin.com/in/johndoe"
    assert c.verification_status == "valid"
    assert c.job_applied_id == a_job.id


def test_find_contacts_empty_results(db, a_job):
    with patch("api.warren.hunter.service.Settings", return_value=_Settings()), \
         patch("api.warren.hunter.service.httpx.get", return_value=_mock_response(emails=[])):
        contacts = HunterService.find_contacts(a_job.id, db)

    assert contacts == []


def test_find_contacts_deduplication(db, a_job):
    emails = [{"value": "jane@acme.com", "first_name": "Jane", "last_name": "Smith", "position": "Hiring Manager"}]

    with patch("api.warren.hunter.service.Settings", return_value=_Settings()), \
         patch("api.warren.hunter.service.httpx.get", return_value=_mock_response(emails=emails)):
        HunterService.find_contacts(a_job.id, db)

    with patch("api.warren.hunter.service.Settings", return_value=_Settings()), \
         patch("api.warren.hunter.service.httpx.get", return_value=_mock_response(emails=emails)):
        HunterService.find_contacts(a_job.id, db)

    from api.dad.outreach import OutreachContact
    count = db.query(OutreachContact).filter(OutreachContact.email == "jane@acme.com").count()
    assert count == 1


def test_find_contacts_missing_optional_fields(db, a_job):
    emails = [{"value": "mystery@acme.com"}]
    with patch("api.warren.hunter.service.Settings", return_value=_Settings()), \
         patch("api.warren.hunter.service.httpx.get", return_value=_mock_response(emails=emails)):
        contacts = HunterService.find_contacts(a_job.id, db)

    assert len(contacts) == 1
    c = contacts[0]
    assert c.first_name == ""
    assert c.last_name == ""
    assert c.position is None
    assert c.hiring_role == HiringRole.engineering_manager
