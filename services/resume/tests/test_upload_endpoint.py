from fastapi.testclient import TestClient

from services.resume.app.api.uploads import minio_store
from services.resume.app.main import app as resume_app
from services.resume.app.repositories.resume_repository import resume_repository


def test_upload_resume_accepts_pdf(monkeypatch):
    resume_repository.reset()
    client = TestClient(resume_app)
    saved_object_keys: list[str] = []

    def fake_put_pdf(*, object_key: str, content: bytes, content_type: str) -> str:
        saved_object_keys.append(object_key)
        assert content.startswith(b"%PDF")
        assert content_type == "application/pdf"
        return object_key

    monkeypatch.setattr(minio_store, "put_pdf", fake_put_pdf)

    response = client.post(
        "/internal/resumes/upload",
        data={"candidate_name": "Test User"},
        files={"file": ("resume.pdf", b"%PDF-1.7\nresume body\n", "application/pdf")},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert response.json()["candidate_name"] == "Test User"
    assert response.json()["content_type"] == "application/pdf"
    assert response.json()["size_bytes"] > 0
    assert response.json()["upload_id"]
    assert saved_object_keys == [response.json()["object_key"]]
