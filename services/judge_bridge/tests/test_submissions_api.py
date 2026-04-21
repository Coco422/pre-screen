from fastapi.testclient import TestClient

from services.judge_bridge.app.main import app as judge_app


def test_run_endpoint_uses_language_map(monkeypatch):
    from services.judge_bridge.app.api import submissions

    class FakeJudge0Client:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def run_sync(self, payload: dict) -> dict:
            assert payload["language_id"] == 71
            assert payload["stdin"] == "demo"
            assert payload["enable_per_process_and_thread_time_limit"] is True
            assert payload["enable_per_process_and_thread_memory_limit"] is True
            return {"stdout": "ok\n", "status": {"id": 3, "description": "Accepted"}}

    monkeypatch.setattr(submissions, "Judge0Client", FakeJudge0Client)
    client = TestClient(judge_app)

    response = client.post(
        "/internal/judge/run",
        json={"language": "python", "source_code": "print('ok')", "stdin": "demo"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "run"
    assert response.json()["stdout"] == "ok\n"


def test_submit_endpoint_returns_scored_summary(monkeypatch):
    from services.judge_bridge.app.api import submissions

    class FakeJudge0Client:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def run_sync(self, payload: dict) -> dict:
            if payload["stdin"] == "1 2":
                return {"stdout": "3\n", "status": {"id": 3, "description": "Accepted"}}
            return {"stdout": "5\n", "status": {"id": 3, "description": "Accepted"}}

    monkeypatch.setattr(submissions, "Judge0Client", FakeJudge0Client)
    client = TestClient(judge_app)

    response = client.post(
        "/internal/judge/submit",
        json={
            "language": "python",
            "source_code": "print('ok')",
            "testcases": [
                {"stdin": "1 2", "expected_stdout": "3\n", "score": 50},
                {"stdin": "2 3", "expected_stdout": "4\n", "score": 50},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "submit"
    assert payload["summary"]["passed_count"] == 1
    assert payload["summary"]["total_score"] == 50


def test_run_endpoint_applies_java_profile(monkeypatch):
    from services.judge_bridge.app.api import submissions

    class FakeJudge0Client:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def run_sync(self, payload: dict) -> dict:
            assert payload["language_id"] == 62
            assert payload["memory_limit"] == 3_145_728
            assert payload["max_processes_and_or_threads"] == 120
            assert payload["enable_per_process_and_thread_time_limit"] is True
            assert payload["enable_per_process_and_thread_memory_limit"] is True
            return {"stdout": "ok\n", "status": {"id": 3, "description": "Accepted"}}

    monkeypatch.setattr(submissions, "Judge0Client", FakeJudge0Client)
    client = TestClient(judge_app)

    response = client.post(
        "/internal/judge/run",
        json={"language": "java", "source_code": "class Main { public static void main(String[] args) {} }"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "run"
