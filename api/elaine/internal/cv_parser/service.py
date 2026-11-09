from fastapi import HTTPException, UploadFile, status

from api.logger import get_logger

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}

log = get_logger(__name__)


class CVParserService:

    @staticmethod
    async def upload(file: UploadFile) -> dict:
        content_type = file.content_type or ""
        filename = file.filename or ""
        extension = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

        if content_type not in ALLOWED_CONTENT_TYPES and extension not in ALLOWED_EXTENSIONS:
            log.warning("cv_upload_invalid_type", extra={"filename": filename, "content_type": content_type})
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must be a PDF or Word document (.pdf, .doc, .docx)",
            )

        contents = await file.read()
        log.info("cv_upload_success", extra={"filename": filename, "size_bytes": len(contents)})
        return {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(contents),
        }
