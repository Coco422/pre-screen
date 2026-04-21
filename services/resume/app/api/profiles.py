from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.resume.app.parsing.profile_builder import build_candidate_profile


class ExtractedPagePayload(BaseModel):
    page_number: int
    text: str


class MultimodalPagePayload(BaseModel):
    page_number: int
    summary: str


class BuildProfileRequest(BaseModel):
    extracted_pages: list[ExtractedPagePayload]
    multimodal_pages: list[MultimodalPagePayload] = Field(default_factory=list)


router = APIRouter(prefix="/internal/resumes", tags=["resume-profiles"])


@router.post("/profiles/build")
async def build_profile(request: BuildProfileRequest) -> dict:
    return build_candidate_profile(
        [page.model_dump() for page in request.extracted_pages],
        [page.model_dump() for page in request.multimodal_pages],
    )
