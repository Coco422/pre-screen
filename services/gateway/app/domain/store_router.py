"""Route gateway store calls between demo memory and postgres repos."""

from __future__ import annotations

from typing import Any

from pre_screen_common.object_store import get_object_store
from pre_screen_common.settings import get_settings
from services.gateway.app.domain.demo_store import gateway_demo_store
from services.gateway.app.repositories.ai_settings_repository import AISettingsRepository
from services.gateway.app.repositories.auth_repository import AuthRepository, ensure_auth_ready
from services.gateway.app.repositories.candidate_repository import CandidateRepository
from services.gateway.app.repositories.exam_repository import ExamRepository
from services.gateway.app.repositories.task_repository import TaskRepository


def use_postgres_store() -> bool:
    try:
        return get_settings().use_postgres_store
    except Exception:
        return False


def bootstrap_postgres_store() -> None:
    if not use_postgres_store():
        return
    ensure_auth_ready()
    try:
        get_object_store().ensure_bucket()
    except Exception:
        pass


class GatewayStoreRouter:
    """Facade preserving demo_store method names for API layer."""

    def login(self, username: str, password: str) -> dict[str, Any]:
        if use_postgres_store():
            return AuthRepository().login(username, password)
        return gateway_demo_store.login(username, password)

    def get_current_user(self, token: str) -> dict[str, Any]:
        if use_postgres_store():
            return AuthRepository().get_current_user(token)
        return gateway_demo_store.get_current_user(token)

    def list_tasks(self, *, status: str | None = None, keyword: str | None = None) -> dict[str, Any]:
        if use_postgres_store():
            return TaskRepository().list_tasks(status=status, keyword=keyword)
        return gateway_demo_store.list_tasks(status=status, keyword=keyword)

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return TaskRepository().create_task(payload)
        return gateway_demo_store.create_task(payload)

    def get_task(self, task_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return TaskRepository().get_task(task_id)
        return gateway_demo_store.get_task(task_id)

    def create_uploads(self, task_id: str, files: list[dict[str, Any]]) -> dict[str, Any]:
        if use_postgres_store():
            return CandidateRepository().create_uploads(task_id, files)
        return gateway_demo_store.create_uploads(task_id, files)

    def get_upload(self, upload_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return CandidateRepository().get_upload(upload_id)
        return gateway_demo_store.get_upload(upload_id)

    def list_candidates(self, **kwargs: Any) -> dict[str, Any]:
        if use_postgres_store():
            return CandidateRepository().list_candidates(**kwargs)
        return gateway_demo_store.list_candidates(**kwargs)

    def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return CandidateRepository().get_candidate(candidate_id)
        return gateway_demo_store.get_candidate(candidate_id)

    def update_candidate(self, candidate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return CandidateRepository().update_candidate(candidate_id, payload)
        return gateway_demo_store.update_candidate(candidate_id, payload)

    def get_candidate_pdf_path(self, candidate_id: str) -> str | None:
        if use_postgres_store():
            return None
        return gateway_demo_store.get_candidate_pdf_path(candidate_id)

    def get_candidate_pdf_payload(self, candidate_id: str) -> dict[str, Any] | None:
        if use_postgres_store():
            return CandidateRepository().get_candidate_pdf_payload(candidate_id)
        path = gateway_demo_store.get_candidate_pdf_path(candidate_id)
        if not path:
            return None
        from pathlib import Path

        return {"content": Path(path).read_bytes(), "filename": Path(path).name}

    def get_dashboard(self) -> dict[str, Any]:
        if use_postgres_store():
            return CandidateRepository().get_dashboard()
        return gateway_demo_store.get_dashboard()

    def get_ai_settings(self) -> dict[str, Any]:
        if use_postgres_store():
            result = AISettingsRepository().get()
            result.pop("_api_key", None)
            return result
        return gateway_demo_store.get_ai_settings()

    def update_ai_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return AISettingsRepository().update(payload)
        return gateway_demo_store.update_ai_settings(payload)

    def test_ai_settings(self) -> dict[str, Any]:
        if use_postgres_store():
            from pre_screen_common.ai_client import AIClient
            import time

            raw = AISettingsRepository().get()
            api_key = raw.get("_api_key") or ""
            base_url = raw.get("base_url") or ""
            model = raw.get("model") or ""
            if not api_key or not base_url or not model:
                return {"ok": False, "error": "AI settings are not fully configured."}
            try:
                client = AIClient(api_key=api_key, base_url=base_url, model=model)
                start = time.time()
                client.simple_text_completion("请回复OK")
                return {"ok": True, "latency_ms": int((time.time() - start) * 1000)}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        return gateway_demo_store.test_ai_settings()

    # --- Exam / paper / results (postgres) ---

    def generate_paper(self, candidate_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().generate_paper(candidate_id)
        return gateway_demo_store.generate_paper(candidate_id)

    def list_papers(self, *, status: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().list_papers(status=status, task_id=task_id)
        return gateway_demo_store.list_papers(status=status, task_id=task_id)

    def get_paper(self, paper_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().get_paper(paper_id)
        return gateway_demo_store.get_paper(paper_id)

    def update_paper(self, paper_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().update_paper(paper_id, payload)
        return gateway_demo_store.update_paper(paper_id, payload)

    def publish_paper(self, paper_id: str, duration_minutes: int | None = None) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().publish_paper(paper_id, duration_minutes)
        return gateway_demo_store.publish_paper(paper_id, duration_minutes)

    def get_exam_payload(self, token: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().get_exam_payload(token)
        return gateway_demo_store.get_exam_payload(token)

    def start_exam(self, token: str, verification_code: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().start_exam(token, verification_code)
        return gateway_demo_store.start_exam(token, verification_code)

    def heartbeat(self, token: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().heartbeat(token)
        return gateway_demo_store.heartbeat(token)

    def save_answer(self, token: str, question_id: str, draft_answer: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().save_answer(token, question_id, draft_answer)
        return gateway_demo_store.save_answer(token, question_id, draft_answer)

    def record_risk_event(self, token: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().record_risk_event(token, event_type, payload)
        return gateway_demo_store.record_risk_event(token, event_type, payload)

    def get_coding_question(self, token: str, question_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().get_coding_question(token, question_id)
        return gateway_demo_store.get_coding_question(token, question_id)

    def store_coding_submission(
        self,
        token: str,
        question_id: str,
        *,
        language: str,
        source_code: str,
        result: dict[str, Any],
    ) -> None:
        if use_postgres_store():
            ExamRepository().store_coding_submission(
                token, question_id, language=language, source_code=source_code, result=result
            )
            return
        gateway_demo_store.store_coding_submission(
            token, question_id, language=language, source_code=source_code, result=result
        )

    def submit_exam(self, token: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().submit_exam(token)
        return gateway_demo_store.submit_exam(token)

    def list_results(self, *, status: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().list_results(status=status, task_id=task_id)
        return gateway_demo_store.list_results(status=status, task_id=task_id)

    def get_result(self, result_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().get_result(result_id)
        return gateway_demo_store.get_result(result_id)

    def review_result(self, result_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().review_result(result_id, payload)
        return gateway_demo_store.review_result(result_id, payload)

    def complete_screening(self, result_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().complete_screening(result_id, payload)
        return gateway_demo_store.complete_screening(result_id, payload)

    def list_monitor_sessions(self) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().list_monitor_sessions()
        return gateway_demo_store.list_monitor_sessions()

    def force_submit_session(self, session_id: str) -> dict[str, Any]:
        if use_postgres_store():
            return ExamRepository().force_submit_session(session_id)
        return gateway_demo_store.force_submit_session(session_id)

    def _require_active_session(self, token: str) -> Any:
        if use_postgres_store():
            return ExamRepository()._require_active_session(token)
        return gateway_demo_store._require_active_session(token)

    def __getattr__(self, name: str) -> Any:
        return getattr(gateway_demo_store, name)


gateway_store = GatewayStoreRouter()
