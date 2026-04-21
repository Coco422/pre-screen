from fastapi.testclient import TestClient

from services.risk.app.main import app as risk_app
from services.risk.app.repositories.event_repository import event_repository


def test_events_api_accepts_risk_event():
    event_repository.reset()
    client = TestClient(risk_app)

    response = client.post(
        "/internal/risk/events",
        json={
            "event_type": "page_blur",
            "session_id": "session-001",
            "payload": {"count": 1},
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert response.json()["event_type"] == "page_blur"
    assert response.json()["session_id"] == "session-001"
