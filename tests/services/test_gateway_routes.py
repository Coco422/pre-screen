from fastapi.testclient import TestClient

from services.gateway.app.main import app


def test_gateway_admin_candidates_endpoint_returns_items():
    client = TestClient(app)

    response = client.get("/admin/candidates")

    assert response.status_code == 200
    assert response.json()["items"]


def test_gateway_public_exam_endpoint_returns_exam_shell_payload():
    client = TestClient(app)

    response = client.get("/public/exams/token-demo")

    assert response.status_code == 200
    assert response.json()["token"] == "token-demo"
    assert response.json()["questions"]


def test_gateway_public_exam_heartbeat_is_accepted():
    client = TestClient(app)

    response = client.post("/public/exams/token-demo/heartbeat")

    assert response.status_code == 202
    assert response.json()["token"] == "token-demo"
    assert response.json()["status"] == "accepted"


def test_gateway_public_exam_answer_save_is_accepted():
    client = TestClient(app)

    response = client.put(
        "/public/exams/token-demo/answers/q-code-1",
        json={"draft_answer": {"code": "print('ok')"}},
    )

    assert response.status_code == 202
    assert response.json()["question_id"] == "q-code-1"
    assert response.json()["status"] == "saved"


def test_gateway_public_exam_risk_event_is_accepted():
    client = TestClient(app)

    response = client.post(
        "/public/exams/token-demo/risk-events",
        json={"event_type": "window_blur", "payload": {"count": 1}},
    )

    assert response.status_code == 202
    assert response.json()["event_type"] == "window_blur"


def test_gateway_public_coding_run_is_proxied(monkeypatch):
    from services.gateway.app.api import public_exam

    class FakeJudge0Client:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def run_sync(self, payload: dict) -> dict:
            assert payload["language_id"] == 63
            assert payload["stdin"] == "[1,1,2]"
            assert payload["enable_per_process_and_thread_time_limit"] is True
            assert payload["enable_per_process_and_thread_memory_limit"] is True
            assert payload["memory_limit"] == 1_048_576
            return {"stdout": "[1,2]\n", "status": {"id": 3, "description": "Accepted"}}

    monkeypatch.setattr(public_exam, "Judge0Client", FakeJudge0Client)
    client = TestClient(app)

    response = client.post(
        "/public/exams/token-demo/coding/run",
        json={"language": "JavaScript", "source_code": "console.log('ok')", "stdin": "[1,1,2]"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "run"
    assert response.json()["stdout"] == "[1,2]\n"


def test_gateway_public_coding_submit_is_scored(monkeypatch):
    from services.gateway.app.api import public_exam

    class FakeJudge0Client:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def run_sync(self, payload: dict) -> dict:
            assert payload["enable_per_process_and_thread_time_limit"] is True
            assert payload["enable_per_process_and_thread_memory_limit"] is True
            if payload["stdin"] == "[1,1,2,3,2]\n":
                return {"stdout": "[1,2,3]\n", "status": {"id": 3, "description": "Accepted"}}
            return {"stdout": "[\"a\",\"b\"]\n", "status": {"id": 3, "description": "Accepted"}}

    monkeypatch.setattr(public_exam, "Judge0Client", FakeJudge0Client)
    client = TestClient(app)

    response = client.post(
        "/public/exams/token-demo/coding/submit",
        json={"question_id": "q-code-1", "language": "javascript", "source_code": "console.log('ok')"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "submit"
    assert response.json()["summary"]["passed_count"] == 1
    assert response.json()["summary"]["total_score"] == 50
