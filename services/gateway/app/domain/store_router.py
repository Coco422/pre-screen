"""Route gateway store calls between demo memory and postgres repos."""

from __future__ import annotations

from typing import Any

from pre_screen_common.object_store import get_object_store
from pre_screen_common.settings import get_settings
from services.gateway.app.domain.demo_store import gateway_demo_store
from services.gateway.app.repositories.ai_settings_repository import AISettingsRepository
from services.gateway.app.repositories.auth_repository import AuthRepository, ensure_auth_ready
from services.gateway.app.repositories.candidate_repository import CandidateRepository
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
        # MinIO may not be ready at first boot; first upload will retry.
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
            # PDF lives in MinIO; use get_candidate_pdf_payload instead.
            return None
        return gateway_demo_store.get_candidate_pdf_path(candidate_id)

    def get_candidate_pdf_payload(self, candidate_id: str) -> dict[str, Any] | None:
        if use_postgres_store():
            return CandidateRepository().get_candidate_pdf_payload(candidate_id)
        path = gateway_demo_store.get_candidate_pdf_path(candidate_id)
        if not path:
            return None
        from pathlib import Path

        data = Path(path).read_bytes()
        return {"content": data, "filename": Path(path).name}

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

    def __getattr__(self, name: str) -> Any:
        return getattr(gateway_demo_store, name)


gateway_store = GatewayStoreRouter()
