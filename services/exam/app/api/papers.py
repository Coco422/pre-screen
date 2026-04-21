from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.exam.app.domain.paper_generator import generate_paper_draft
from services.exam.app.repositories.exam_repository import exam_repository


class BuildDraftRequest(BaseModel):
    job_template: dict
    jd_text: str
    candidate_profile: dict = Field(default_factory=dict)


router = APIRouter(prefix="/internal/papers", tags=["exam-papers"])


@router.post("/draft")
async def create_draft(request: BuildDraftRequest) -> dict:
    draft = generate_paper_draft(
        job_template=request.job_template,
        jd_text=request.jd_text,
        candidate_profile=request.candidate_profile,
    )
    return exam_repository.save_paper_draft(draft)
