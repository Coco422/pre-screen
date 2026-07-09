"""Integration: durable upload/candidate path (STORE_BACKEND=postgres)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import fitz
import psycopg
import pytest
from fastapi.testclient import TestClient

DSN = os.environ.get(
    "POSTGRES_DSN_TEST",
    "postgresql://postgres:postgres@localhost:5432/prescreen",
)


def _can_connect() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select 1
                    from information_schema.tables
                    where table_schema = 'resume' and table_name = 'upload_jobs'
                    """
                )
                return cur.fetchone() is not None
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_connect(),
    reason="Postgres resume tables not available (run flyway-migrate)",
)


def _pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "姓名: 持久化候选人\nSkills: Python Vue\n项目: 在线考试系统")
    return document.tobytes()


@pytest.fixture()
def postgres_client(monkeypatch):
    monkeypatch.setenv("STORE_BACKEND", "postgres")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql+psycopg://postgres:postgres@localhost:5432/prescreen")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_BUCKET_RESUMES", "resumes")
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://192.168.100.189:2360")
    monkeypatch.setenv("AI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("AI_API_KEY", "test-key")

    from pre_screen_common.db import reset_engine_cache
    from pre_screen_common.settings import reset_settings_cache

    reset_settings_cache()
    reset_engine_cache()

    from services.gateway.app.domain import store_router
    from services.gateway.app.main import app
    from services.gateway.app.repositories.auth_repository import ensure_auth_ready

    # Force re-read settings in router helpers.
    ensure_auth_ready()

    client = TestClient(app)
    yield client

    reset_settings_cache()
    reset_engine_cache()


def test_upload_and_candidate_survive_store_reload(postgres_client, monkeypatch):
    from services.gateway.app.domain import resume_intelligence
    from services.gateway.app.repositories import candidate_repository as candidate_repo_mod

    def fake_parse_resume_file(pdf_path, render_dir=None):
        del render_dir
        assert Path(pdf_path).exists()
        return {
            "name": "持久化候选人",
            "email": "persist@example.com",
            "skills": ["Python", "Vue"],
            "raw_text": "项目: 在线考试系统",
            "page_metrics": [{"page_number": 1, "text_chars": 120, "image_count": 0, "needs_multimodal": False}],
            "source_summary": {"multimodal_pages": []},
        }

    def fake_enrich(profile, image_paths=None):
        del image_paths
        return {
            "display_name": profile["name"],
            "email": profile["email"],
            "phone": "13800000000",
            "city": "深圳",
            "skills": profile["skills"],
            "profile_summary": "解析完成",
            "project_summary": "有在线考试系统经验",
            "strengths": ["前端"],
            "risks": [],
            "focus_topics": ["Vue"],
            "recommended_languages": ["TypeScript"],
            "projects": [],
            "missing_fields": [],
        }

    monkeypatch.setattr(candidate_repo_mod, "parse_resume_file", fake_parse_resume_file)
    monkeypatch.setattr(candidate_repo_mod, "enrich_resume_profile", fake_enrich)
    monkeypatch.setattr(resume_intelligence, "enrich_resume_profile", fake_enrich)

    client = postgres_client

    login = client.post("/admin/session/login", json={"username": "hr-demo", "password": "demo-pass"})
    assert login.status_code == 200

    create = client.post(
        "/admin/tasks",
        json={
            "title": "持久化任务",
            "department": "研发",
            "city": "深圳",
            "jd_text": "需要 Vue",
            "tags": ["Vue"],
            "template_config": {
                "base_info_count": 1,
                "objective_count": 1,
                "subjective_count": 1,
                "coding_count": 0,
            },
            "duration_minutes": 60,
        },
    )
    assert create.status_code == 201, create.text
    task_id = create.json()["task_id"]

    upload = client.post(
        f"/admin/tasks/{task_id}/uploads",
        files=[("files", ("resume.pdf", _pdf_bytes(), "application/pdf"))],
    )
    assert upload.status_code == 202, upload.text
    upload_id = upload.json()["items"][0]["upload_id"]
    candidate_id = upload.json()["items"][0]["candidate_id"]

    deadline = time.time() + 15
    parsed = None
    while time.time() < deadline:
        status = client.get(f"/admin/uploads/{upload_id}")
        assert status.status_code == 200
        body = status.json()
        if body["status"] == "parsed" or (body.get("processing") or {}).get("status") == "succeeded":
            parsed = body
            break
        if body["status"] == "failed":
            raise AssertionError(body)
        time.sleep(0.1)
    assert parsed is not None, "upload did not parse in time"

    detail = client.get(f"/admin/candidates/{candidate_id}")
    assert detail.status_code == 200
    assert detail.json()["name"]
    assert detail.json()["resume_pdf_url"] == f"/admin/candidates/{candidate_id}/resume.pdf"

    pdf = client.get(f"/admin/candidates/{candidate_id}/resume.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert len(pdf.content) > 100

    # Simulate process restart: new repository instance still sees rows.
    from services.gateway.app.repositories.candidate_repository import CandidateRepository

    repo = CandidateRepository()
    again = repo.get_candidate(candidate_id)
    assert again["id"] == candidate_id
    assert again["task_id"] == task_id
    payload = repo.get_candidate_pdf_payload(candidate_id)
    assert payload is not None
    assert payload["content"] == pdf.content
