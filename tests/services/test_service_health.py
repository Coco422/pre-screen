from fastapi.testclient import TestClient

from services.gateway.app.main import app as gateway_app
from services.resume.app.main import app as resume_app
from services.exam.app.main import app as exam_app
from services.judge_bridge.app.main import app as judge_app
from services.scoring.app.main import app as scoring_app
from services.risk.app.main import app as risk_app


def test_gateway_health():
    assert TestClient(gateway_app).get("/healthz").json()["service"] == "gateway"


def test_resume_health():
    assert TestClient(resume_app).get("/healthz").json()["service"] == "resume"


def test_exam_health():
    assert TestClient(exam_app).get("/healthz").json()["service"] == "exam"


def test_judge_bridge_health():
    assert TestClient(judge_app).get("/healthz").json()["service"] == "judge-bridge"


def test_scoring_health():
    assert TestClient(scoring_app).get("/healthz").json()["service"] == "scoring"


def test_risk_health():
    assert TestClient(risk_app).get("/healthz").json()["service"] == "risk"
