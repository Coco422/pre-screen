import time
from threading import Event

import fitz
import pytest
from fastapi.testclient import TestClient

from services.gateway.app.domain.demo_store import gateway_demo_store
from services.gateway.app.main import app


@pytest.fixture(autouse=True)
def reset_gateway_demo_store():
    gateway_demo_store.reset()
    yield
    gateway_demo_store.reset()


def _build_resume_pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "\n".join(
            [
                "姓名: 测试候选人",
                "Email: candidate@example.com",
                "城市: 深圳",
                "Skills: Python Vue JavaScript TypeScript",
                "项目经历: 做过后台管理系统和在线考试系统。",
            ]
        ),
    )
    return document.tobytes()


def _wait_for_upload_ready(client: TestClient, upload_id: str, timeout_seconds: float = 3.0) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/admin/uploads/{upload_id}")
        assert response.status_code == 200
        payload = response.json()
        processing = payload.get("processing") or {}
        if processing.get("status") == "succeeded" or payload["status"] == "parsed":
            return payload
        time.sleep(0.02)
    raise AssertionError(f"upload {upload_id} did not reach parsed state")


def test_gateway_admin_candidates_endpoint_returns_items():
    client = TestClient(app)

    response = client.get("/admin/candidates")

    assert response.status_code == 200
    assert response.json()["items"]


def test_gateway_candidates_endpoint_filters_and_returns_workbench_fields():
    client = TestClient(app)

    pending_response = client.get(
        "/admin/candidates",
        params={
            "pending_review": "true",
            "sort_by": "resume_uploaded_at",
            "order": "asc",
        },
    )

    assert pending_response.status_code == 200
    pending_payload = pending_response.json()
    assert [item["id"] for item in pending_payload["items"]] == ["c-002"]
    assert pending_payload["items"][0]["resume_parse_status"] == "parsed"
    assert pending_payload["items"][0]["screening_status"] == "待审核"
    assert pending_payload["items"][0]["risk_flag"] == "需核实"
    assert pending_payload["items"][0]["resume_uploaded_at"]
    assert pending_payload["items"][0]["updated_at"]
    assert pending_payload["items"][0]["next_action"] == {
        "label": "查看详情",
        "target": "/admin/candidates/c-002",
    }

    published_response = client.get(
        "/admin/candidates",
        params={
            "role": "前端开发工程师",
            "paper_sent": "true",
            "sort_by": "updated_at",
            "order": "desc",
        },
    )

    assert published_response.status_code == 200
    published_items = published_response.json()["items"]
    assert [item["id"] for item in published_items] == ["c-004", "c-003"]
    assert all(item["paper_sent"] for item in published_items)
    assert published_items[0]["next_action"]["label"] == "结果复核"

    risk_response = client.get("/admin/candidates", params={"risk_level": "high"})

    assert risk_response.status_code == 200
    assert [item["id"] for item in risk_response.json()["items"]] == ["c-004"]


def test_gateway_dashboard_endpoint_returns_metrics_and_priority_lists():
    client = TestClient(app)

    response = client.get("/admin/dashboard")

    assert response.status_code == 200
    payload = response.json()

    assert payload["metrics"] == {
        "screening_candidate_count": 1,
        "pending_publish_count": 1,
        "exam_in_progress_count": 1,
        "submitted_count": 1,
        "screening_completed_count": 1,
    }

    assert [item["candidate_id"] for item in payload["screening_candidates"]] == ["c-002"]
    assert payload["screening_candidates"][0]["status"] == "待审核"
    assert payload["pending_publish_candidates"][0]["candidate_id"] == "c-001"
    assert payload["submitted_results"][0]["candidate_id"] == "c-004"
    assert payload["submitted_results"][0]["status"] == "已交卷"


def test_gateway_public_exam_endpoint_returns_exam_shell_payload():
    client = TestClient(app)

    response = client.get("/public/exams/token-demo")

    assert response.status_code == 200
    assert response.json()["token"] == "token-demo"
    assert response.json()["questions"]


def test_gateway_hr_to_exam_review_flow(monkeypatch):
    from services.gateway.app.api import public_exam
    from services.gateway.app.domain import demo_store

    def fake_parse_resume_file(pdf_path, render_dir=None):
        del pdf_path, render_dir
        return {
            "name": "测试候选人",
            "email": "candidate@example.com",
            "skills": ["Python", "Vue", "JavaScript", "TypeScript"],
            "raw_text": "测试候选人 有 Vue 与 JavaScript 项目经验",
            "page_metrics": [
                {
                    "page_number": 1,
                    "text_chars": 128,
                    "image_count": 0,
                    "needs_multimodal": False,
                }
            ],
            "source_summary": {"multimodal_pages": []},
        }

    class FakeJudge0Client:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def run_sync(self, payload: dict) -> dict:
            assert payload["enable_per_process_and_thread_time_limit"] is True
            assert payload["enable_per_process_and_thread_memory_limit"] is True
            if payload["stdin"] == "[1,1,2]\n":
                return {"stdout": "[1,2]\n", "status": {"id": 3, "description": "Accepted"}}
            if payload["stdin"] == "[1,1,2,3,2]\n":
                return {"stdout": "[1,2,3]\n", "status": {"id": 3, "description": "Accepted"}}
            if payload["stdin"] == "[\"a\",\"a\",\"b\",\"c\",\"b\"]\n":
                return {
                    "stdout": "[\"a\",\"b\",\"c\"]\n",
                    "status": {"id": 3, "description": "Accepted"},
                }
            raise AssertionError(f"unexpected stdin: {payload['stdin']}")

    monkeypatch.setattr(demo_store, "parse_resume_file", fake_parse_resume_file)
    monkeypatch.setattr(public_exam, "Judge0Client", FakeJudge0Client)
    client = TestClient(app)

    login_response = client.post(
        "/admin/session/login",
        json={"username": "hr-demo", "password": "demo-pass"},
    )

    assert login_response.status_code == 200
    auth_token = login_response.json()["token"]
    assert login_response.json()["user"]["role"] == "hr"

    me_response = client.get(
        "/admin/session/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "hr-demo"

    create_job_response = client.post(
        "/admin/tasks",
        json={
            "title": "前端工程师",
            "department": "平台研发",
            "city": "深圳",
            "jd_text": "需要 Vue、TypeScript、JavaScript 能力，负责在线考试与后台系统。",
            "tags": ["Vue", "TypeScript", "frontend"],
            "template_config": {
                "base_info_count": 1,
                "objective_count": 2,
                "subjective_count": 1,
                "coding_count": 1,
            },
            "duration_minutes": 75,
        },
    )

    assert create_job_response.status_code == 201
    task_id = create_job_response.json()["task_id"]

    list_jobs_response = client.get("/admin/tasks", params={"keyword": "前端", "status": "open"})

    assert list_jobs_response.status_code == 200
    assert list_jobs_response.json()["total"] >= 1
    assert any(item["task_id"] == task_id for item in list_jobs_response.json()["items"])

    task_detail_response = client.get(f"/admin/tasks/{task_id}")

    assert task_detail_response.status_code == 200
    assert task_detail_response.json()["task_id"] == task_id

    upload_response = client.post(
        f"/admin/tasks/{task_id}/uploads",
        files=[
            ("files", ("resume-1.pdf", _build_resume_pdf_bytes(), "application/pdf")),
            ("files", ("resume-2.pdf", _build_resume_pdf_bytes(), "application/pdf")),
        ],
    )

    assert upload_response.status_code == 202
    assert len(upload_response.json()["items"]) == 2
    assert all(item["status"] == "queued" for item in upload_response.json()["items"])
    upload_id = upload_response.json()["items"][0]["upload_id"]
    candidate_id = upload_response.json()["items"][0]["candidate_id"]

    upload_status = _wait_for_upload_ready(client, upload_id)

    assert upload_status["candidate_id"] == candidate_id
    assert upload_status["status"] == "parsed"

    candidates_response = client.get(
        "/admin/candidates",
        params={"task_id": task_id, "status": "待发卷"},
    )

    assert candidates_response.status_code == 200
    assert any(item["id"] == candidate_id for item in candidates_response.json()["items"])

    candidate_detail_response = client.get(f"/admin/candidates/{candidate_id}")

    assert candidate_detail_response.status_code == 200
    assert candidate_detail_response.json()["email"] == "candidate@example.com"

    candidate_update_response = client.put(
        f"/admin/candidates/{candidate_id}",
        json={
            "city": "杭州",
            "skills": ["Vue", "TypeScript", "JavaScript"],
            "project_summary": "已人工确认候选人项目经历与在线考试场景高度相关。",
            "review_note": "HR 已完成首轮画像修正。",
        },
    )

    assert candidate_update_response.status_code == 200
    assert candidate_update_response.json()["city"] == "杭州"
    assert "HR 已完成首轮画像修正。" in candidate_update_response.json()["review_notes"]

    generate_paper_response = client.post(f"/admin/candidates/{candidate_id}/papers/generate")

    assert generate_paper_response.status_code == 201
    generated_paper = generate_paper_response.json()
    paper_id = generated_paper["paper_id"]

    paper_detail_response = client.get(f"/admin/papers/{paper_id}")

    assert paper_detail_response.status_code == 200
    assert paper_detail_response.json()["paper_id"] == paper_id
    assert paper_detail_response.json()["mix"]["coding"] == 1

    paper_update_response = client.put(
        f"/admin/papers/{paper_id}",
        json={"title": "前端工程师在线测评（正式版）"},
    )

    assert paper_update_response.status_code == 200
    assert paper_update_response.json()["title"] == "前端工程师在线测评（正式版）"

    publish_response = client.post(
        f"/admin/papers/{paper_id}/publish",
        json={"duration_minutes": 75},
    )

    assert publish_response.status_code == 201
    published = publish_response.json()
    token = published["token"]
    verification_code = published["verification_code"]
    assert published["exam_url"].endswith(token)

    access_response = client.get(f"/public/exams/{token}/access")
    assert access_response.status_code == 404

    exam_not_started_response = client.get(f"/public/exams/{token}")

    assert exam_not_started_response.status_code == 200
    assert exam_not_started_response.json()["access_state"] == "not_started"
    assert exam_not_started_response.json()["questions"] == []

    invalid_start_response = client.post(f"/public/exams/{token}/start", json={"verification_code": "000000"})

    assert invalid_start_response.status_code == 403

    start_response = client.post(f"/public/exams/{token}/start", json={"verification_code": verification_code})

    assert start_response.status_code == 201
    assert start_response.json()["status"] == "in_progress"
    session_id = start_response.json()["session_id"]

    exam_shell_response = client.get(f"/public/exams/{token}")

    assert exam_shell_response.status_code == 200
    shell_payload = exam_shell_response.json()
    assert shell_payload["token"] == token
    assert shell_payload["access_state"] == "in_progress"
    assert len(shell_payload["questions"]) == 5

    base_info_id = next(item["id"] for item in generated_paper["questions"] if item["kind"] == "base_info")
    objective_question = next(
        item
        for item in generated_paper["questions"]
        if item["kind"] == "objective" and "Vue" in item["title"]
    )
    objective_id = objective_question["id"]
    subjective_id = next(item["id"] for item in generated_paper["questions"] if item["kind"] == "subjective")
    coding_id = next(item["id"] for item in generated_paper["questions"] if item["kind"] == "coding")

    base_info_save_response = client.put(
        f"/public/exams/{token}/answers/{base_info_id}",
        json={"draft_answer": {"姓名": "测试候选人", "可到岗时间": "两周"}},
    )
    objective_save_response = client.put(
        f"/public/exams/{token}/answers/{objective_id}",
        json={"draft_answer": {"answer": "Proxy 劫持并按依赖触发更新"}},
    )
    subjective_save_response = client.put(
        f"/public/exams/{token}/answers/{subjective_id}",
        json={
            "draft_answer": {
                "answer_text": "我在在线考试项目中负责 Vue 前端架构、性能优化和问题排查，持续复盘系统质量。"
            }
        },
    )

    assert base_info_save_response.status_code == 202
    assert objective_save_response.status_code == 202
    assert subjective_save_response.status_code == 202

    heartbeat_response = client.post(f"/public/exams/{token}/heartbeat")
    risk_response = client.post(
        f"/public/exams/{token}/risk-events",
        json={"event_type": "window_blur", "payload": {"count": 1}},
    )

    assert heartbeat_response.status_code == 202
    assert risk_response.status_code == 202

    run_response = client.post(
        f"/public/exams/{token}/coding/run",
        json={
            "language": "JavaScript",
            "source_code": "console.log('ok')",
            "stdin": "[1,1,2]\n",
        },
    )

    assert run_response.status_code == 200
    assert run_response.json()["mode"] == "run"
    assert run_response.json()["stdout"] == "[1,2]\n"

    coding_submit_response = client.post(
        f"/public/exams/{token}/coding/submit",
        json={
            "question_id": coding_id,
            "language": "javascript",
            "source_code": "console.log('ok')",
        },
    )

    assert coding_submit_response.status_code == 200
    assert coding_submit_response.json()["summary"]["passed_count"] == 2
    assert coding_submit_response.json()["summary"]["total_score"] == 100

    submit_exam_response = client.post(f"/public/exams/{token}/submit")

    assert submit_exam_response.status_code == 200
    assert submit_exam_response.json()["status"] == "completed"
    assert submit_exam_response.json()["session_id"] == session_id
    result_id = submit_exam_response.json()["result_id"]
    assert submit_exam_response.json()["summary"]["objective_score"] == 5
    assert submit_exam_response.json()["summary"]["coding_score"] == 100
    assert submit_exam_response.json()["summary"]["risk_summary"]["event_count"] == 1

    completed_submissions_response = client.get(
        "/admin/results",
        params={"status": "completed", "task_id": task_id},
    )

    assert completed_submissions_response.status_code == 200
    assert any(item["result_id"] == result_id for item in completed_submissions_response.json()["items"])

    submission_detail_response = client.get(f"/admin/results/{result_id}")

    assert submission_detail_response.status_code == 200
    assert submission_detail_response.json()["candidate"]["id"] == candidate_id
    assert submission_detail_response.json()["paper"]["paper_id"] == paper_id
    assert submission_detail_response.json()["summary"]["total_score"] >= 105
    assert submission_detail_response.json()["risk_events"][0]["event_type"] == "window_blur"

    exam_submitted_response = client.get(f"/public/exams/{token}")

    assert exam_submitted_response.status_code == 200
    assert exam_submitted_response.json()["access_state"] == "submitted"


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


def test_gateway_upload_exposes_processing_and_structured_projects(monkeypatch):
    from services.gateway.app.domain import demo_store

    def fake_parse_resume_file(pdf_path, render_dir=None):
        del pdf_path, render_dir
        return {
            "name": "梁承与",
            "email": "candidate@example.com",
            "skills": ["Vue", "TypeScript", "JavaScript"],
            "raw_text": "智慧物流供应链管理系统，Vue 前端知识库管理系统",
            "page_metrics": [
                {
                    "page_number": 1,
                    "text_chars": 1600,
                    "image_count": 0,
                    "needs_multimodal": False,
                }
            ],
            "source_summary": {"multimodal_pages": []},
        }

    def fake_enrich_resume_profile(profile, image_paths=None):
        del image_paths
        return {
            "display_name": profile["name"],
            "email": profile["email"],
            "phone": "13047369113",
            "city": "深圳",
            "skills": profile["skills"],
            "profile_summary": "候选人在后台权限、联调和前端工程化方面表达完整。",
            "project_summary": "有两个完整的 B 端项目，适合围绕权限控制、接口联调和工程化出题。",
            "strengths": ["做过动态路由与权限控制", "熟悉 Axios 拦截器与 Token 刷新"],
            "risks": ["实习经历较少"],
            "focus_topics": ["权限控制", "Token 刷新", "工程化"],
            "recommended_languages": ["JavaScript", "TypeScript", "Python"],
            "projects": [
                {
                    "project_id": "proj-1",
                    "name": "智慧物流供应链管理系统",
                    "role": "前端开发",
                    "summary": "负责权限分配、动态路由和表格交互。",
                    "tech_stack": ["Vue3", "TypeScript", "Pinia", "Element Plus"],
                    "responsibilities": ["动态路由与权限控制", "请求层封装", "复杂业务表格"],
                    "achievements": ["实现按钮级权限控制", "提升后台交互效率"],
                    "metrics": ["多条件检索", "跨页多选"],
                    "source_pages": [1],
                    "confidence": "high",
                }
            ],
        }

    monkeypatch.setattr(demo_store, "parse_resume_file", fake_parse_resume_file)
    monkeypatch.setattr(demo_store, "enrich_resume_profile", fake_enrich_resume_profile)
    client = TestClient(app)

    create_job_response = client.post(
        "/admin/tasks",
        json={
            "title": "前端工程师",
            "department": "平台研发",
            "city": "深圳",
            "jd_text": "需要 Vue、TypeScript、JavaScript 能力，负责后台权限控制。",
            "tags": ["Vue", "TypeScript", "frontend"],
            "template_config": {
                "base_info_count": 1,
                "objective_count": 2,
                "subjective_count": 1,
                "coding_count": 1,
            },
            "duration_minutes": 75,
        },
    )

    task_id = create_job_response.json()["task_id"]
    upload_response = client.post(
        f"/admin/tasks/{task_id}/uploads",
        files=[("files", ("resume.pdf", _build_resume_pdf_bytes(), "application/pdf"))],
    )

    upload_id = upload_response.json()["items"][0]["upload_id"]
    candidate_id = upload_response.json()["items"][0]["candidate_id"]

    upload_status = _wait_for_upload_ready(client, upload_id)
    candidate_detail_response = client.get(f"/admin/candidates/{candidate_id}")

    assert upload_status["processing"]["stage"] == "profile_ready"
    assert upload_status["processing"]["steps"]["project_extract"]["status"] == "succeeded"
    assert upload_status["processing"]["message"]
    assert candidate_detail_response.status_code == 200
    assert candidate_detail_response.json()["projects"][0]["name"] == "智慧物流供应链管理系统"
    assert candidate_detail_response.json()["processing"]["stage"] == "profile_ready"
    assert candidate_detail_response.json()["analysis"]["focus_topics"] == ["权限控制", "Token 刷新", "工程化"]


def test_gateway_upload_exposes_project_extraction_stage_while_enrichment_runs(monkeypatch):
    from services.gateway.app.domain import demo_store

    enrichment_started = Event()
    allow_enrichment_finish = Event()

    def fake_parse_resume_file(pdf_path, render_dir=None):
        del pdf_path, render_dir
        return {
            "name": "测试候选人",
            "email": "candidate@example.com",
            "skills": ["Vue", "TypeScript"],
            "raw_text": "项目经历: 权限系统, 在线考试平台",
            "page_metrics": [
                {
                    "page_number": 1,
                    "text_chars": 1200,
                    "image_count": 0,
                    "needs_multimodal": False,
                }
            ],
            "source_summary": {"multimodal_pages": []},
        }

    def fake_enrich_resume_profile(profile, image_paths=None):
        del profile, image_paths
        enrichment_started.set()
        allow_enrichment_finish.wait(timeout=1)
        return {
            "display_name": "测试候选人",
            "email": "candidate@example.com",
            "phone": "13000000000",
            "city": "深圳",
            "skills": ["Vue", "TypeScript"],
            "profile_summary": "画像整理完成。",
            "project_summary": "有权限与考试平台项目经验。",
            "strengths": ["做过后台系统"],
            "risks": [],
            "focus_topics": ["权限控制"],
            "recommended_languages": ["TypeScript"],
            "projects": [],
        }

    monkeypatch.setattr(demo_store, "parse_resume_file", fake_parse_resume_file)
    monkeypatch.setattr(demo_store, "enrich_resume_profile", fake_enrich_resume_profile)
    client = TestClient(app)

    create_job_response = client.post(
        "/admin/tasks",
        json={
            "title": "前端工程师",
            "department": "平台研发",
            "city": "深圳",
            "jd_text": "需要 Vue、TypeScript 能力。",
            "tags": ["Vue", "TypeScript"],
            "template_config": {
                "base_info_count": 1,
                "objective_count": 2,
                "subjective_count": 1,
                "coding_count": 1,
            },
            "duration_minutes": 60,
        },
    )

    task_id = create_job_response.json()["task_id"]
    upload_response = client.post(
        f"/admin/tasks/{task_id}/uploads",
        files=[("files", ("resume.pdf", _build_resume_pdf_bytes(), "application/pdf"))],
    )
    upload_id = upload_response.json()["items"][0]["upload_id"]

    interim_payload = None
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if enrichment_started.is_set():
            response = client.get(f"/admin/uploads/{upload_id}")
            assert response.status_code == 200
            payload = response.json()
            if payload.get("processing", {}).get("stage") == "project_extract":
                interim_payload = payload
                break
        time.sleep(0.02)

    allow_enrichment_finish.set()

    assert interim_payload is not None
    assert interim_payload["processing"]["status"] == "running"
    assert interim_payload["processing"]["steps"]["pdf_parse"]["status"] == "succeeded"
    assert interim_payload["processing"]["steps"]["project_extract"]["status"] == "running"
    assert "项目经历" in interim_payload["processing"]["message"]

    final_payload = _wait_for_upload_ready(client, upload_id)
    assert final_payload["processing"]["stage"] == "profile_ready"


def test_generated_paper_links_questions_to_resume_projects(monkeypatch):
    from services.gateway.app.domain import demo_store

    def fake_parse_resume_file(pdf_path, render_dir=None):
        del pdf_path, render_dir
        return {
            "name": "郭子贤",
            "email": "candidate@example.com",
            "skills": ["Python", "Java", "Vue"],
            "raw_text": "基于RAG的通用智能AI助教，智能运维管理平台",
            "page_metrics": [
                {
                    "page_number": 1,
                    "text_chars": 1600,
                    "image_count": 0,
                    "needs_multimodal": False,
                }
            ],
            "source_summary": {"multimodal_pages": []},
        }

    def fake_enrich_resume_profile(profile, image_paths=None):
        del image_paths
        return {
            "display_name": profile["name"],
            "email": profile["email"],
            "phone": "15099970619",
            "city": "广州",
            "skills": profile["skills"],
            "profile_summary": "候选人做过 RAG 和告警通知相关项目。",
            "project_summary": "项目经历覆盖 RAG 系统、告警通知、接口编排与联调。",
            "strengths": ["熟悉 RAG", "有通知模块经验"],
            "risks": [],
            "focus_topics": ["RAG 检索", "告警通知", "接口编排"],
            "recommended_languages": ["Python", "JavaScript"],
            "projects": [
                {
                    "project_id": "proj-1",
                    "name": "基于RAG的通用智能AI助教",
                    "role": "毕业设计",
                    "summary": "支持上传文档并进行问答。",
                    "tech_stack": ["Python", "LangChain", "Chroma"],
                    "responsibilities": ["RAG 检索增强", "多轮评估", "飞书机器人接入"],
                    "achievements": ["提升复杂问题准确率"],
                    "metrics": ["三种检索模式"],
                    "source_pages": [1],
                    "confidence": "high",
                }
            ],
        }

    def fake_build_question_brief(*, candidate_profile, job_context):
        del job_context
        assert candidate_profile["projects"][0]["name"] == "基于RAG的通用智能AI助教"
        return {
            "introduction": "题目围绕 RAG 项目、接口编排与通知链路展开。",
            "focus_topics": ["RAG 检索", "接口编排"],
            "subjective_questions": [
                {
                    "title": "围绕「基于RAG的通用智能AI助教」说明你的检索链路设计",
                    "description": "重点说明你如何做检索召回、结果重排与答案生成。",
                    "rubric_text": "RAG 检索 重排 Prompt 数据验证 复盘",
                    "score": 20,
                }
            ],
            "coding_theme": "notification_dedupe",
            "coding_language": "Python",
            "generation_notes": ["题目已与候选人 RAG 项目建立关联。"],
        }

    monkeypatch.setattr(demo_store, "parse_resume_file", fake_parse_resume_file)
    monkeypatch.setattr(demo_store, "enrich_resume_profile", fake_enrich_resume_profile)
    monkeypatch.setattr(demo_store, "build_question_brief", fake_build_question_brief)
    client = TestClient(app)

    create_job_response = client.post(
        "/admin/tasks",
        json={
            "title": "AI 应用工程师",
            "department": "平台研发",
            "city": "深圳",
            "jd_text": "需要做 RAG、接口编排和应用落地。",
            "tags": ["Python", "RAG", "backend"],
            "template_config": {
                "base_info_count": 1,
                "objective_count": 2,
                "subjective_count": 1,
                "coding_count": 1,
            },
            "duration_minutes": 90,
        },
    )

    task_id = create_job_response.json()["task_id"]
    upload_response = client.post(
        f"/admin/tasks/{task_id}/uploads",
        files=[("files", ("resume.pdf", _build_resume_pdf_bytes(), "application/pdf"))],
    )
    upload_id = upload_response.json()["items"][0]["upload_id"]
    candidate_id = upload_response.json()["items"][0]["candidate_id"]
    _wait_for_upload_ready(client, upload_id)

    generate_paper_response = client.post(f"/admin/candidates/{candidate_id}/papers/generate")
    assert generate_paper_response.status_code == 201

    paper_id = generate_paper_response.json()["paper_id"]
    paper_detail_response = client.get(f"/admin/papers/{paper_id}")
    payload = paper_detail_response.json()

    subjective_questions = [item for item in payload["questions"] if item["kind"] == "subjective"]
    coding_questions = [item for item in payload["questions"] if item["kind"] == "coding"]

    assert payload["generation_summary"]["matched_projects"] == ["基于RAG的通用智能AI助教"]
    assert any("基于RAG的通用智能AI助教" in item["title"] for item in subjective_questions)
    assert coding_questions[0]["language"] == "Python"
    assert "告警" in coding_questions[0]["description"] or "通知" in coding_questions[0]["description"]
