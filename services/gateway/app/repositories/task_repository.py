from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from pre_screen_common.db import db_connection
from pre_screen_common.settings import AppSettings


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


def _as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


class TaskRepository:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings

    def _next_id(self, kind: str, prefix: str) -> str:
        with db_connection(settings=self._settings) as conn:
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

    def list_tasks(self, *, status: str | None = None, keyword: str | None = None) -> dict[str, Any]:
        clauses = ["1=1"]
        params: dict[str, Any] = {}
        if status:
            clauses.append("t.status = :status")
            params["status"] = status
        if keyword:
            clauses.append("(t.title ilike :kw or t.department ilike :kw or t.city ilike :kw)")
            params["kw"] = f"%{keyword}%"

        sql = f"""
            select t.*,
              (select count(*) from resume.candidates c
                where c.task_id = t.id) as candidate_count,
              (select count(*) from resume.upload_jobs u
                where u.task_id = t.id) as upload_count
            from app.screening_tasks t
            where {' and '.join(clauses)}
            order by t.created_at desc
        """
        with db_connection(settings=self._settings) as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        items = [
            {
                "id": row["id"],
                "title": row["title"],
                "role": row["department"] or row["city"] or "",
                "status": row["status"],
                "candidate_count": int(row["candidate_count"] or 0),
                "upload_count": int(row["upload_count"] or 0),
                "created_at": _isoformat(row["created_at"]),
            }
            for row in rows
        ]
        return {"items": items, "total": len(items)}

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = self._next_id("task", "t")
        now = datetime.now(UTC)
        with db_connection(settings=self._settings) as conn:
            conn.execute(
                text(
                    """
                    insert into app.screening_tasks (
                      id, title, department, city, jd_text, tags, template_config,
                      duration_minutes, status, created_at, updated_at
                    ) values (
                      :id, :title, :department, :city, :jd_text, cast(:tags as jsonb),
                      cast(:template_config as jsonb), :duration_minutes, 'open',
                      :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": task_id,
                    "title": payload["title"],
                    "department": payload.get("department", ""),
                    "city": payload.get("city", ""),
                    "jd_text": payload.get("jd_text", ""),
                    "tags": _as_json(payload.get("tags") or []),
                    "template_config": _as_json(payload.get("template_config") or {}),
                    "duration_minutes": int(payload.get("duration_minutes") or 90),
                    "created_at": now,
                    "updated_at": now,
                },
            )
        return {
            "task_id": task_id,
            "title": payload["title"],
            "department": payload.get("department", ""),
            "city": payload.get("city", ""),
            "status": "open",
            "created_at": _isoformat(now),
        }

    def get_task(self, task_id: str) -> dict[str, Any]:
        with db_connection(settings=self._settings) as conn:
            row = conn.execute(
                text("select * from app.screening_tasks where id = :id"),
                {"id": task_id},
            ).mappings().first()
            if row is None:
                raise LookupError("Task not found.")
            uploads = conn.execute(
                text(
                    """
                    select id, task_id, candidate_id, file_name, status, progress, error,
                           processing, created_at, updated_at
                    from resume.upload_jobs
                    where task_id = :task_id
                    order by created_at desc
                    """
                ),
                {"task_id": task_id},
            ).mappings().all()
            candidates = conn.execute(
                text(
                    """
                    select external_id, name, role, screening_status, city
                    from resume.candidates
                    where task_id = :task_id
                    order by updated_at desc
                    """
                ),
                {"task_id": task_id},
            ).mappings().all()

        return {
            "task_id": row["id"],
            "title": row["title"],
            "department": row["department"],
            "city": row["city"],
            "jd_text": row["jd_text"],
            "tags": _from_json(row["tags"], []),
            "template_config": _from_json(row["template_config"], {}),
            "duration_minutes": row["duration_minutes"],
            "status": row["status"],
            "created_at": _isoformat(row["created_at"]),
            "uploads": [
                {
                    "upload_id": u["id"],
                    "task_id": u["task_id"],
                    "candidate_id": u["candidate_id"],
                    "filename": u["file_name"],
                    "status": u["status"],
                    "progress": u["progress"],
                    "error": u["error"],
                    "processing": _from_json(u["processing"], {}),
                    "created_at": _isoformat(u["created_at"]),
                    "updated_at": _isoformat(u["updated_at"]),
                }
                for u in uploads
            ],
            "candidates": [
                {
                    "candidate_id": c["external_id"],
                    "name": c["name"],
                    "role": c["role"],
                    "status": c["screening_status"],
                    "city": c["city"],
                }
                for c in candidates
            ],
        }
