from __future__ import annotations

from sqlalchemy import text

from pre_screen_common.db import db_connection
from pre_screen_common.settings import AppSettings


def next_text_id(kind: str, prefix: str, *, settings: AppSettings | None = None) -> str:
    with db_connection(settings=settings) as conn:
        conn.execute(
            text(
                """
                insert into app.id_counters (kind, value)
                values (:kind, 1)
                on conflict (kind) do update set value = app.id_counters.value + 1
                """
            ),
            {"kind": kind},
        )
        value = conn.execute(
            text("select value from app.id_counters where kind = :kind"),
            {"kind": kind},
        ).scalar_one()
        return f"{prefix}-{int(value):03d}"
