import base64
from email.mime.text import MIMEText

from fastapi import HTTPException, status
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from api.logger import get_logger
from api.warren.config import Settings

log = get_logger(__name__)


class GmailService:

    @staticmethod
    def _get_service():
        settings = Settings()
        if not all([settings.GMAIL_CLIENT_ID, settings.GMAIL_CLIENT_SECRET, settings.GMAIL_REFRESH_TOKEN]):
            log.error("gmail_credentials_missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gmail credentials are not configured",
            )
        credentials = Credentials(
            token=None,
            refresh_token=settings.GMAIL_REFRESH_TOKEN,
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token",
        )
        try:
            return build("gmail", "v1", credentials=credentials)
        except Exception as exc:
            log.error("gmail_service_build_failed", extra={"error": str(exc)})
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to connect to Gmail")

    @staticmethod
    def create_draft(to_email: str, subject: str, body: str) -> str:
        service = GmailService._get_service()

        message = MIMEText(body, "plain")
        message["to"] = to_email
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            draft = service.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw}},
            ).execute()
        except Exception as exc:
            log.error("gmail_draft_create_failed", extra={"to_email": to_email, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to create Gmail draft")

        log.info("gmail_draft_created", extra={"to_email": to_email, "draft_id": draft["id"]})
        return draft["id"]
