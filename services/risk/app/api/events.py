from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from services.risk.app.repositories.event_repository import event_repository


class CreateEventRequest(BaseModel):
    event_type: str
    session_id: str
    payload: dict = Field(default_factory=dict)


router = APIRouter(prefix="/internal/risk", tags=["risk"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def create_event(request: CreateEventRequest) -> dict:
    event = event_repository.create(
        event_type=request.event_type,
        session_id=request.session_id,
        payload=request.payload,
    )
    return {
        "status": "accepted",
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "session_id": event["session_id"],
    }
