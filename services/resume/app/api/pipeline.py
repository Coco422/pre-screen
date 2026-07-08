from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.resume.app.domain.models import AvatarAsset, ResumeParseResult
from services.resume.app.repositories.resume_repository import resume_repository
from services.resume.app.tasks.batch_extract import run_resume_batch
from services.resume.app.tasks.parse_resume import parse_resume_file

router = APIRouter(prefix="/internal", tags=["resume-pipeline"])


class ParseResumeRequest(BaseModel):
    use_ai: bool = True


class CreateBatchRequest(BaseModel):
    local_paths: list[str] = Field(default_factory=list)
    use_ai: bool = True
    batch_id: str | None = None


@router.post("/resumes/{file_id}/parse")
async def parse_resume(file_id: str, request: ParseResumeRequest | None = None) -> dict:
    upload = resume_repository.get_upload(file_id)
    if upload is None or not upload.local_path:
        raise HTTPException(status_code=404, detail="Resume file not found.")
    pdf_path = Path(upload.local_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Local resume copy is missing.")

    render_dir = Path("tmp/resume-renders") / file_id
    profile = parse_resume_file(
        pdf_path,
        render_dir=render_dir,
        use_ai=request.use_ai if request else True,
    )
    if not profile.get("name"):
        profile["name"] = upload.candidate_name
    avatar = AvatarAsset(**profile["avatar"])
    result = ResumeParseResult(
        file_id=file_id,
        candidate_name=profile.get("name") or upload.candidate_name,
        original_filename=upload.original_filename,
        markdown=profile["markdown"],
        profile=profile,
        metadata=profile["metadata"],
        avatar=avatar,
        pdf_path=upload.local_path,
    )
    resume_repository.save_parse_result(result)
    return _parse_result_payload(result)


@router.get("/resumes/{file_id}/markdown")
async def get_resume_markdown(file_id: str) -> dict:
    result = resume_repository.get_parse_result(file_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Parsed resume not found.")
    return {"file_id": file_id, "markdown": result.markdown}


@router.get("/resumes/{file_id}/assets/avatar")
async def get_resume_avatar(file_id: str) -> dict:
    result = resume_repository.get_parse_result(file_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Parsed resume not found.")
    payload = _avatar_payload(result.avatar)
    if result.avatar.status == "found":
        payload["asset_url"] = f"/internal/resumes/{file_id}/assets/avatar/file"
    return payload


@router.get("/resumes/{file_id}/assets/avatar/file")
async def get_resume_avatar_file(file_id: str) -> FileResponse:
    result = resume_repository.get_parse_result(file_id)
    if result is None or not result.avatar.image_path:
        raise HTTPException(status_code=404, detail="Avatar asset not found.")
    return FileResponse(result.avatar.image_path)


@router.post("/resumes/batches")
async def create_resume_batch(request: CreateBatchRequest) -> dict:
    pdf_paths = [Path(path) for path in request.local_paths]
    missing = [str(path) for path in pdf_paths if not path.exists()]
    if missing:
        raise HTTPException(status_code=400, detail={"missing_paths": missing})
    result = run_resume_batch(
        pdf_paths=pdf_paths,
        batch_id=request.batch_id,
        use_ai=request.use_ai,
        save_to_repository=True,
    )
    return {
        "batch_id": result.batch_id,
        "file_ids": list(result.file_ids),
        "output_dir": result.output_dir,
        "analysis_markdown": result.analysis_markdown,
    }


@router.get("/resume-batches/{batch_id}/analysis")
async def get_resume_batch_analysis(batch_id: str) -> dict:
    result = resume_repository.get_batch_result(batch_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resume batch not found.")
    return {
        "batch_id": result.batch_id,
        "output_dir": result.output_dir,
        "analysis_markdown": result.analysis_markdown,
    }


def _parse_result_payload(result: ResumeParseResult) -> dict:
    return {
        "file_id": result.file_id,
        "candidate_name": result.candidate_name,
        "parse_status": result.parse_status,
        "profile": result.profile,
        "metadata": result.metadata,
        "avatar": _avatar_payload(result.avatar),
    }


def _avatar_payload(avatar: AvatarAsset) -> dict:
    return {
        "status": avatar.status,
        "page_number": avatar.page_number,
        "xref": avatar.xref,
        "bbox": avatar.bbox,
        "image_path": avatar.image_path,
        "width": avatar.width,
        "height": avatar.height,
        "reason": avatar.reason,
    }
