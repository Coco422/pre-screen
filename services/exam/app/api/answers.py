from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.exam.app.repositories.exam_repository import exam_repository


class SaveAnswerRequest(BaseModel):
    draft_answer: dict


router = APIRouter(prefix="/internal/exam/sessions", tags=["exam-answers"])


@router.put("/{session_id}/answers/{question_id}", status_code=status.HTTP_202_ACCEPTED)
async def save_answer(session_id: str, question_id: str, request: SaveAnswerRequest) -> dict:
    session = exam_repository.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return exam_repository.save_answer_draft(
        session_id=session_id,
        question_id=question_id,
        draft_answer=request.draft_answer,
    )
