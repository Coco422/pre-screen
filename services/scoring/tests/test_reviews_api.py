from fastapi.testclient import TestClient

from services.scoring.app.main import app as scoring_app


def test_reviews_api_returns_subjective_suggestions_and_score_summary():
    client = TestClient(scoring_app)

    response = client.post(
        "/internal/scoring/reviews/suggest",
        json={
            "objective_score": 20,
            "coding_score": 40,
            "risk_summary": {"blur": 2},
            "subjective_answers": [
                {
                    "question_title": "请复盘一个你最熟悉的项目",
                    "answer_text": "我负责后台管理系统，重点优化了权限与性能，并复盘了上线故障。",
                    "rubric_text": "关注项目完整性、技术深度、问题复盘。",
                    "max_score": 20,
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggestions"][0]["question_title"] == "请复盘一个你最熟悉的项目"
    assert payload["summary"]["objective_score"] == 20
    assert payload["summary"]["coding_score"] == 40
    assert payload["summary"]["total_score"] >= 60
