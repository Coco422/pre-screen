from __future__ import annotations

from typing import Any

from sqlalchemy import text

from pre_screen_common.db import db_connection
from pre_screen_common.settings import AppSettings, get_settings


class AISettingsRepository:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings

    def get(self) -> dict[str, Any]:
        settings = self._settings or get_settings()
        with db_connection(settings=settings) as conn:
            row = conn.execute(text("select base_url, model, api_key from app.ai_settings where id = 1")).mappings().first()
        if row is None:
            api_key = settings.ai_api_key
            base_url = settings.ai_base_url
            model = settings.ai_model
        else:
            api_key = row["api_key"] or settings.ai_api_key
            base_url = row["base_url"] or settings.ai_base_url
            model = row["model"] or settings.ai_model
        if api_key and len(api_key) > 4:
            masked = f"sk-****{api_key[-4:]}"
        elif api_key:
            masked = "sk-****"
        else:
            masked = ""
        return {
            "base_url": base_url,
            "model": model,
            "api_key_masked": masked,
            "configured": bool(api_key and base_url),
            "_api_key": api_key,
        }

    def update(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get()
        base_url = payload.get("base_url", current["base_url"])
        model = payload.get("model", current["model"])
        api_key = payload.get("api_key", current.get("_api_key", ""))
        with db_connection(settings=self._settings) as conn:
            conn.execute(
                text(
                    """
                    insert into app.ai_settings (id, base_url, model, api_key, updated_at)
                    values (1, :base_url, :model, :api_key, now())
                    on conflict (id) do update set
                      base_url = excluded.base_url,
                      model = excluded.model,
                      api_key = excluded.api_key,
                      updated_at = now()
                    """
                ),
                {"base_url": base_url or "", "model": model or "", "api_key": api_key or ""},
            )
        public = self.get()
        public.pop("_api_key", None)
        return public
