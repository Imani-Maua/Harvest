from fastapi import HTTPException, UploadFile, status

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


class CVParserService:

    @staticmethod
    async def upload(file: UploadFile) -> dict:
        content_type = file.content_type or ""
        filename = file.filename or ""
        extension = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

        if content_type not in ALLOWED_CONTENT_TYPES and extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must be a PDF or Word document (.pdf, .doc, .docx)",
            )

        contents = await file.read()
        return {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(contents),
        }
