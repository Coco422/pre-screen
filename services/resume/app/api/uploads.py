from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from services.resume.app.domain.models import ResumeUpload
from services.resume.app.repositories.resume_repository import resume_repository
from services.resume.app.storage.minio_store import minio_store

router = APIRouter(prefix="/internal/resumes", tags=["resumes"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    candidate_name: str = Form(...), file: UploadFile = File(...)
) -> dict[str, str | int]:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only application/pdf uploads are supported.",
        )

    content = await file.read()
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded content must start with a PDF header.",
        )

    upload_id = uuid4().hex
    object_key = f"resumes/{upload_id}.pdf"
    content_type = file.content_type
    minio_store.put_pdf(object_key=object_key, content=content, content_type=content_type)
    local_path = Path("tmp/resume-uploads") / f"{upload_id}.pdf"
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)

    upload = ResumeUpload(
        upload_id=upload_id,
        candidate_name=candidate_name,
        original_filename=file.filename or "resume.pdf",
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(content),
        local_path=str(local_path),
    )
    resume_repository.save_upload(upload)

    return {
        "candidate_name": upload.candidate_name,
        "status": "accepted",
        "file_id": upload.upload_id,
        "upload_id": upload.upload_id,
        "object_key": upload.object_key,
        "content_type": upload.content_type,
        "size_bytes": upload.size_bytes,
    }
