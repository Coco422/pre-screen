"""Durable paper → exam → result → review loop under STORE_BACKEND=postgres."""

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
SCRATCH = Path(
    os.environ.get(
        "GOAL_SCRATCH",
        "/var/folders/5b/xw60dn9d5wvfl40dxn5xzzr00000gp/T/grok-goal-132d6d578722/implementer",
    )
)


def _can_connect() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select 1 from information_schema.tables
                    where table_schema = 'exam' and table_name = 'papers'
                    """
                )
                return cur.fetchone() is not None
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _can_connect(), reason="exam schema not migrated")


def _pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "姓名: 闭环候选人\nSkills: Vue TypeScript\n项目: 招聘预筛系统")
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
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("AI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("AI_API_KEY", "test-key")

    from pre_screen_common.db import reset_engine_cache
    from pre_screen_common.settings import reset_settings_cache

    reset_settings_cache()
    reset_engine_cache()

    from services.gateway.app.main import app
    from services.gateway.app.repositories.auth_repository import ensure_auth_ready

    ensure_auth_ready()
    yield TestClient(app)
    reset_settings_cache()
    reset_engine_cache()


def _wait_upload(client: TestClient, upload_id: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/admin/uploads/{upload_id}").json()
        if body["status"] == "parsed" or (body.get("processing") or {}).get("status") == "succeeded":
            return body
        if body["status"] == "failed":
            raise AssertionError(body)
        time.sleep(0.05)
    raise AssertionError(f"upload {upload_id} not parsed")


def _wait_paper(client: TestClient, candidate_id: str, timeout: float = 30.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        detail = client.get(f"/admin/candidates/{candidate_id}").json()
        paper_id = detail.get("paper_id")
        status = detail.get("status")
        processing = detail.get("processing") or {}
        if paper_id and status == "待发卷":
            return paper_id
        if processing.get("status") == "failed":
            raise AssertionError(processing)
        time.sleep(0.05)
    raise AssertionError("paper not ready")


def test_durable_paper_exam_review_loop(postgres_client, monkeypatch):
    from services.gateway.app.repositories import candidate_repository as cand_mod
    from services.gateway.app.repositories import exam_repository as exam_mod
    from services.gateway.app.domain import resume_intelligence

    def fake_parse(pdf_path, render_dir=None):
        del render_dir
        assert Path(pdf_path).exists()
        return {
            "name": "闭环候选人",
            "email": "loop@example.com",
            "skills": ["Vue", "TypeScript"],
            "raw_text": "项目: 招聘预筛系统",
            "page_metrics": [
                {"page_number": 1, "text_chars": 200, "image_count": 0, "needs_multimodal": False}
            ],
            "source_summary": {"multimodal_pages": []},
        }

    def fake_enrich(profile, image_paths=None):
        del image_paths
        return {
            "display_name": profile["name"],
            "email": profile["email"],
            "phone": "13900000000",
            "city": "深圳",
            "skills": profile["skills"],
            "profile_summary": "画像完成",
            "project_summary": "做过招聘预筛系统",
            "strengths": ["前端"],
            "risks": [],
            "focus_topics": ["Vue"],
            "recommended_languages": ["TypeScript"],
            "projects": [
                {
                    "project_id": "p1",
                    "name": "招聘预筛系统",
                    "role": "前端",
                    "summary": "负责考试页",
                    "tech_stack": ["Vue"],
                    "responsibilities": ["页面开发"],
                    "achievements": [],
                    "metrics": [],
                    "source_pages": [1],
                    "confidence": "high",
                }
            ],
            "missing_fields": [],
        }

    def fake_brief(*, candidate_profile, job_context):
        del job_context
        assert candidate_profile["skills"]
        return {
            "introduction": "围绕招聘预筛系统出题。",
            "focus_topics": ["Vue"],
            "subjective_questions": [
                {
                    "title": "说明你在招聘预筛系统中的职责",
                    "description": "结合真实项目",
                    "rubric_text": "项目 技术 结果",
                    "score": 20,
                }
            ],
            "coding_theme": "notification_dedupe",
            "coding_language": "JavaScript",
            "generation_notes": ["ok"],
        }

    monkeypatch.setattr(cand_mod, "parse_resume_file", fake_parse)
    monkeypatch.setattr(cand_mod, "enrich_resume_profile", fake_enrich)
    monkeypatch.setattr(resume_intelligence, "enrich_resume_profile", fake_enrich)
    monkeypatch.setattr(exam_mod, "build_question_brief", fake_brief)
    monkeypatch.setattr(resume_intelligence, "build_question_brief", fake_brief)

    client = postgres_client
    log_lines: list[str] = []

    login = client.post("/admin/session/login", json={"username": "hr-demo", "password": "demo-pass"})
    assert login.status_code == 200
    log_lines.append(f"login={login.status_code}")

    create = client.post(
        "/admin/tasks",
        json={
            "title": "闭环筛选任务",
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
            "duration_minutes": 45,
        },
    )
    assert create.status_code == 201, create.text
    task_id = create.json()["task_id"]
    log_lines.append(f"task_id={task_id}")

    upload = client.post(
        f"/admin/tasks/{task_id}/uploads",
        files=[("files", ("resume.pdf", _pdf_bytes(), "application/pdf"))],
    )
    assert upload.status_code == 202, upload.text
    upload_id = upload.json()["items"][0]["upload_id"]
    candidate_id = upload.json()["items"][0]["candidate_id"]
    _wait_upload(client, upload_id)
    log_lines.append(f"candidate_id={candidate_id} upload_parsed")

    gen = client.post(f"/admin/candidates/{candidate_id}/papers/generate")
    assert gen.status_code == 202, gen.text
    paper_id = _wait_paper(client, candidate_id)
    log_lines.append(f"paper_id={paper_id}")

    # Process boundary: new repository instance still sees paper.
    from services.gateway.app.repositories.exam_repository import ExamRepository

    paper_again = ExamRepository().get_paper(paper_id)
    assert paper_again["paper_id"] == paper_id
    assert paper_again["status"] == "draft"
    assert paper_again["candidate_id"] == candidate_id

    updated = client.put(f"/admin/papers/{paper_id}", json={"title": "闭环正式卷"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "闭环正式卷"
    assert ExamRepository().get_paper(paper_id)["title"] == "闭环正式卷"

    publish = client.post(f"/admin/papers/{paper_id}/publish", json={"duration_minutes": 45})
    assert publish.status_code == 201, publish.text
    token = publish.json()["token"]
    code = publish.json()["verification_code"]
    log_lines.append(f"token={token} code={code}")

    inv_paper = ExamRepository().get_paper(paper_id)
    assert inv_paper["status"] == "published"
    assert inv_paper["invitation"]["token"] == token

    start = client.post(f"/public/exams/{token}/start", json={"verification_code": code})
    assert start.status_code == 201, start.text
    session_id = start.json()["session_id"]

    shell = client.get(f"/public/exams/{token}")
    assert shell.status_code == 200
    assert shell.json()["access_state"] == "in_progress"
    questions = shell.json()["questions"]
    assert questions
    q0 = questions[0]["id"]

    save = client.put(
        f"/public/exams/{token}/answers/{q0}",
        json={"draft_answer": {"姓名": "闭环候选人"}},
    )
    assert save.status_code == 202
    hb = client.post(f"/public/exams/{token}/heartbeat")
    assert hb.status_code == 202
    risk = client.post(
        f"/public/exams/{token}/risk-events",
        json={"event_type": "window_blur", "payload": {"n": 1}},
    )
    assert risk.status_code == 202

    # Objective answer if present
    for q in questions:
        if q["kind"] == "objective":
            paper_detail = ExamRepository().get_paper(paper_id)
            full_q = next(item for item in paper_detail["questions"] if item["id"] == q["id"])
            client.put(
                f"/public/exams/{token}/answers/{q['id']}",
                json={"draft_answer": {"answer": full_q.get("answer_key")}},
            )
        if q["kind"] == "subjective":
            client.put(
                f"/public/exams/{token}/answers/{q['id']}",
                json={"draft_answer": {"answer_text": "我在项目中负责 Vue 考试页与状态管理。"}},
            )

    submit = client.post(f"/public/exams/{token}/submit")
    assert submit.status_code == 200, submit.text
    result_id = submit.json()["result_id"]
    assert submit.json()["status"] == "completed"
    assert "summary" in submit.json()
    log_lines.append(f"result_id={result_id} total={submit.json()['summary']['total_score']}")

    # New repo instance after submit
    result_repo = ExamRepository().get_result(result_id)
    assert result_repo["result_id"] == result_id
    assert result_repo["status"] == "completed"
    assert result_repo["summary"]["total_score"] is not None

    listed = ExamRepository().list_results(task_id=task_id)
    assert any(item["result_id"] == result_id for item in listed["items"])

    review = client.put(
        f"/admin/results/{result_id}/review",
        json={"final_subjective_score": 18, "review_notes": ["人工调分"]},
    )
    assert review.status_code == 200, review.text

    complete = client.post(
        f"/admin/results/{result_id}/complete-screening",
        json={"decision": "reject", "review_notes": ["不匹配岗位"]},
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["decision"] == "reject"

    # Survive process boundary
    final = ExamRepository().get_result(result_id)
    assert final["screening_status"] == "reject" or final.get("screening_status") == "reject"
    assert final["review_status"] == "reviewed"
    assert final["summary"]["subjective_score"] == 18

    cand = ExamRepository  # silence linter
    from services.gateway.app.repositories.candidate_repository import CandidateRepository

    cand_final = CandidateRepository().get_candidate(candidate_id)
    assert cand_final["status"] == "已淘汰"
    log_lines.append(f"candidate_status={cand_final['status']}")

    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / "durable-exam-loop.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (SCRATCH / "durable-review.log").write_text(
        f"result_id={result_id}\nreview_status={final['review_status']}\n"
        f"screening_status={final.get('screening_status')}\n"
        f"subjective_score={final['summary']['subjective_score']}\n"
        f"candidate_status={cand_final['status']}\n",
        encoding="utf-8",
    )
    (SCRATCH / "judge0-note.txt").write_text(
        "Coding path not exercised in this loop (coding_count=0); Judge0 not required.\n",
        encoding="utf-8",
    )
