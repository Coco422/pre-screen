"""Route gateway store calls between demo memory and postgres repos."""

from __future__ import annotations

from typing import Any

from pre_screen_common.settings import get_settings
from services.gateway.app.domain.demo_store import gateway_demo_store
from services.gateway.app.repositories.ai_settings_repository import AISettingsRepository
from services.gateway.app.repositories.auth_repository import AuthRepository, ensure_auth_ready
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
        # Reuse demo path which constructs AIClient from env/settings.
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
