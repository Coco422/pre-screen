from fastapi.testclient import TestClient

from services.exam.app.main import app as exam_app
from services.exam.app.repositories.exam_repository import exam_repository


def test_exam_invitation_session_and_answer_flow():
    exam_repository.reset()
    client = TestClient(exam_app)

    invitation_response = client.post(
        "/internal/exam/invitations",
        json={"exam_paper_id": "paper-001", "duration_minutes": 90},
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()
    assert invitation["exam_paper_id"] == "paper-001"
    assert invitation["one_time_code"]
    assert invitation["access_token"]

    session_response = client.post(
        "/internal/exam/sessions/start",
        json={
            "invitation_id": invitation["invitation_id"],
            "one_time_code": invitation["one_time_code"],
        },
    )
    assert session_response.status_code == 201
    session = session_response.json()
    assert session["status"] == "in_progress"
    assert session["expire_at"] > session["start_at"]

    heartbeat_response = client.post(f"/internal/exam/sessions/{session['session_id']}/heartbeat")
    assert heartbeat_response.status_code == 202
    assert heartbeat_response.json()["status"] == "in_progress"

    answer_response = client.put(
        f"/internal/exam/sessions/{session['session_id']}/answers/q-001",
        json={"draft_answer": {"text": "候选人的草稿答案"}},
    )
    assert answer_response.status_code == 202
    answer_payload = answer_response.json()
    assert answer_payload["question_id"] == "q-001"
    assert answer_payload["status"] == "saved"
