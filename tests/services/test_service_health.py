from fastapi.testclient import TestClient

from services.gateway.app.main import app as gateway_app
from services.resume.app.main import app as resume_app
from services.exam.app.main import app as exam_app
from services.judge_bridge.app.main import app as judge_app
from services.scoring.app.main import app as scoring_app
from services.risk.app.main import app as risk_app


def test_gateway_health():
    response = TestClient(gateway_app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"service": "gateway", "status": "ok"}


def test_resume_health():
    response = TestClient(resume_app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"service": "resume", "status": "ok"}


def test_exam_health():
    response = TestClient(exam_app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"service": "exam", "status": "ok"}


def test_judge_bridge_health():
    response = TestClient(judge_app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"service": "judge-bridge", "status": "ok"}


def test_scoring_health():
    response = TestClient(scoring_app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"service": "scoring", "status": "ok"}


def test_risk_health():
    response = TestClient(risk_app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"service": "risk", "status": "ok"}
