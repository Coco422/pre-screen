from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.exam.app.domain.session_rules import compute_exam_window
from services.exam.app.repositories.exam_repository import exam_repository


class StartSessionRequest(BaseModel):
    invitation_id: str
    one_time_code: str


router = APIRouter(prefix="/internal/exam/sessions", tags=["exam-sessions"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_session(request: StartSessionRequest) -> dict:
    invitation = exam_repository.get_invitation(request.invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    if not exam_repository.verify_invitation_code(request.invitation_id, request.one_time_code):
        raise HTTPException(status_code=403, detail="One-time code is invalid.")

    start_at = datetime.now(UTC)
    expire_at = compute_exam_window(start_at, invitation["duration_minutes"])
    return exam_repository.create_session(
        invitation_id=request.invitation_id,
        start_at=start_at,
        expire_at=expire_at,
    )


@router.post("/{session_id}/heartbeat", status_code=status.HTTP_202_ACCEPTED)
async def heartbeat(session_id: str) -> dict:
    session = exam_repository.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return exam_repository.touch_heartbeat(session_id)
