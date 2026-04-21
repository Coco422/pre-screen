from datetime import UTC, datetime
from uuid import uuid4


class EventRepository:
    def __init__(self) -> None:
        self._events: list[dict] = []

    def reset(self) -> None:
        self._events.clear()

    def create(self, *, event_type: str, session_id: str, payload: dict | None = None) -> dict:
        event = {
            "event_id": uuid4().hex,
            "event_type": event_type,
            "session_id": session_id,
            "payload": payload or {},
            "created_at": datetime.now(UTC),
        }
        self._events.append(event)
        return event


event_repository = EventRepository()
