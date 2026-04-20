from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from services.exam.app.repositories.exam_repository import exam_repository


class CreateInvitationRequest(BaseModel):
    exam_paper_id: str
    duration_minutes: int = Field(default=90, ge=1, le=240)


router = APIRouter(prefix="/internal/exam/invitations", tags=["exam-invitations"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_invitation(request: CreateInvitationRequest) -> dict:
    return exam_repository.create_invitation(
        exam_paper_id=request.exam_paper_id,
        duration_minutes=request.duration_minutes,
    )
