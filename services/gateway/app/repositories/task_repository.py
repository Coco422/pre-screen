from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from pre_screen_common.db import db_connection
from pre_screen_common.settings import AppSettings
from services.gateway.app.repositories.candidate_repository import CandidateRepository
from services.gateway.app.repositories.ids import next_text_id
from services.gateway.app.repositories.json_util import as_json as _as_json
from services.gateway.app.repositories.json_util import from_json as _from_json
from services.gateway.app.repositories.json_util import isoformat as _isoformat


class TaskRepository:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings

    def _next_id(self, kind: str, prefix: str) -> str:
        return next_text_id(kind, prefix, settings=self._settings)

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
        candidate_items = CandidateRepository(settings=self._settings).list_candidates(task_id=task_id)[
            "items"
        ]

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
            "candidates": candidate_items,
        }
