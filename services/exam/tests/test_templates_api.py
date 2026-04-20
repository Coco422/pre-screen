from fastapi.testclient import TestClient

from services.exam.app.main import app as exam_app
from services.exam.app.repositories.exam_repository import exam_repository


def test_templates_api_supports_create_list_get_and_clone():
    exam_repository.reset()
    client = TestClient(exam_app)

    create_response = client.post(
        "/internal/exam/templates",
        json={
            "name": "frontend-intern",
            "role_type": "frontend",
            "level": "intern",
            "template_config": {
                "objective_count": 4,
                "subjective_count": 2,
                "coding_count": 1,
            },
            "tags": ["vue", "typescript"],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "frontend-intern"
    assert created["template_config"]["coding_count"] == 1

    list_response = client.get("/internal/exam/templates")
    assert list_response.status_code == 200
    templates = list_response.json()["items"]
    assert len(templates) == 1

    get_response = client.get(f"/internal/exam/templates/{created['template_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["role_type"] == "frontend"

    clone_response = client.post(
        f"/internal/exam/templates/{created['template_id']}/clone",
        json={"name": "frontend-intern-copy"},
    )
    assert clone_response.status_code == 201
    clone = clone_response.json()
    assert clone["name"] == "frontend-intern-copy"
    assert clone["copied_from_template_id"] == created["template_id"]


def test_papers_api_exposes_draft_endpoint_on_planned_path():
    client = TestClient(exam_app)

    response = client.post(
        "/internal/papers/draft",
        json={
            "job_template": {
                "name": "frontend-intern",
                "objective_count": 4,
                "subjective_count": 2,
                "coding_count": 1,
            },
            "jd_text": "前端工程师，需要熟悉 Vue、TypeScript、工程化。",
            "candidate_profile": {"skills": ["Vue", "TypeScript"]},
        },
    )

    assert response.status_code == 200
    assert response.json()["template_name"] == "frontend-intern"
