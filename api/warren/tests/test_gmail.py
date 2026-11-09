from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.warren.gmail.service import GmailService


class _FullSettings:
    GMAIL_CLIENT_ID = "client-id"
    GMAIL_CLIENT_SECRET = "client-secret"
    GMAIL_REFRESH_TOKEN = "refresh-token"


def test_get_service_503_missing_client_id():
    class _S:
        GMAIL_CLIENT_ID = ""
        GMAIL_CLIENT_SECRET = "secret"
        GMAIL_REFRESH_TOKEN = "token"

    with patch("api.warren.gmail.service.Settings", return_value=_S()):
        with pytest.raises(HTTPException) as exc:
            GmailService._get_service()
    assert exc.value.status_code == 503


def test_get_service_503_missing_client_secret():
    class _S:
        GMAIL_CLIENT_ID = "id"
        GMAIL_CLIENT_SECRET = ""
        GMAIL_REFRESH_TOKEN = "token"

    with patch("api.warren.gmail.service.Settings", return_value=_S()):
        with pytest.raises(HTTPException) as exc:
            GmailService._get_service()
    assert exc.value.status_code == 503


def test_get_service_503_missing_refresh_token():
    class _S:
        GMAIL_CLIENT_ID = "id"
        GMAIL_CLIENT_SECRET = "secret"
        GMAIL_REFRESH_TOKEN = ""

    with patch("api.warren.gmail.service.Settings", return_value=_S()):
        with pytest.raises(HTTPException) as exc:
            GmailService._get_service()
    assert exc.value.status_code == 503


def test_create_draft_returns_draft_id():
    mock_service = MagicMock()
    mock_service.users.return_value.drafts.return_value.create.return_value.execute.return_value = {
        "id": "draft-abc-123"
    }

    with patch("api.warren.gmail.service.Settings", return_value=_FullSettings()), \
         patch("api.warren.gmail.service.build", return_value=mock_service):
        result = GmailService.create_draft("to@example.com", "Subject", "Body text")

    assert result == "draft-abc-123"


def test_create_draft_calls_gmail_api_with_correct_args():
    mock_service = MagicMock()
    mock_service.users.return_value.drafts.return_value.create.return_value.execute.return_value = {
        "id": "draft-xyz"
    }

    with patch("api.warren.gmail.service.Settings", return_value=_FullSettings()), \
         patch("api.warren.gmail.service.build", return_value=mock_service):
        GmailService.create_draft("to@example.com", "My Subject", "Hello")

    create_call = mock_service.users.return_value.drafts.return_value.create
    call_kwargs = create_call.call_args.kwargs
    assert call_kwargs["userId"] == "me"
    assert "message" in call_kwargs["body"]
    assert "raw" in call_kwargs["body"]["message"]
    assert call_kwargs["body"]["message"]["raw"]  # non-empty base64 string
