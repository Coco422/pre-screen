from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Thread
from typing import Any

from sqlalchemy import text

from pre_screen_common.db import db_connection
from pre_screen_common.object_store import ObjectStore, get_object_store
from pre_screen_common.settings import AppSettings, get_settings
from services.gateway.app.domain.demo_store import _build_processing
from services.gateway.app.domain.resume_intelligence import enrich_resume_profile
from services.gateway.app.repositories.ids import next_text_id
from services.gateway.app.repositories.json_util import as_json, from_json, isoformat
from services.resume.app.tasks.parse_resume import parse_resume_file


class CandidateRepository:
    def __init__(
        self,
        settings: AppSettings | None = None,
        object_store: ObjectStore | None = None,
    ) -> None:
        self._settings = settings
        self._object_store = object_store

    @property
    def settings(self) -> AppSettings:
        return self._settings or get_settings()

    @property
    def object_store(self) -> ObjectStore:
        return self._object_store or get_object_store()

    def create_uploads(self, task_id: str, files: list[dict[str, Any]]) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            task = conn.execute(
                text("select id, title, city from app.screening_tasks where id = :id"),
                {"id": task_id},
            ).mappings().first()
        if task is None:
            raise LookupError("Task not found.")

        created: list[dict[str, Any]] = []
        for file_item in files:
            filename = file_item["filename"]
            content = file_item["content"]
            if not str(filename).lower().endswith(".pdf"):
                raise ValueError("Only PDF uploads are supported.")

            candidate_id = next_text_id("candidate", "c", settings=self.settings)
            upload_id = next_text_id("upload", "u", settings=self.settings)
            object_key = f"tasks/{task_id}/{candidate_id}/{upload_id}.pdf"
            bucket, object_key = self.object_store.put_bytes(
                object_key=object_key,
                content=content,
                content_type="application/pdf",
            )
            now = datetime.now(UTC)
            processing = _build_processing(
                stage="uploaded",
                status="queued",
                progress=5,
                message="PDF 已写入对象存储，等待解析。",
                step_statuses={"upload": "succeeded", "pdf_parse": "running"},
            )
            profile_json = {
                "summary": "简历已上传，系统正在整理文本、项目经历与出题方向。",
                "project_summary": "解析中，暂无候选人画像。",
                "parse_metrics": {
                    "first_page_characters": 0,
                    "multimodal_pages": 0,
                    "confidence": "待解析",
                },
                "paper_ids": [],
                "latest_upload_id": upload_id,
            }
            with db_connection(settings=self.settings) as conn:
                conn.execute(
                    text(
                        """
                        insert into resume.candidates (
                          external_id, task_id, name, role, city, email, phone,
                          status, screening_status, quality, skills, hobbies,
                          profile_json, analysis_json, projects_json, review_notes,
                          created_at, updated_at
                        ) values (
                          :external_id, :task_id, :name, :role, :city, null, null,
                          'parsing', :screening_status, :quality, cast(:skills as jsonb),
                          cast(:hobbies as jsonb), cast(:profile_json as jsonb),
                          cast(:analysis_json as jsonb), cast(:projects_json as jsonb),
                          cast(:review_notes as jsonb), :created_at, :updated_at
                        )
                        """
                    ),
                    {
                        "external_id": candidate_id,
                        "task_id": task_id,
                        "name": Path(filename).stem,
                        "role": task["title"],
                        "city": task["city"] or "",
                        "screening_status": "解析中",
                        "quality": "待解析",
                        "skills": as_json([]),
                        "hobbies": as_json([]),
                        "profile_json": as_json(profile_json),
                        "analysis_json": as_json(
                            {
                                "focus_topics": [],
                                "strengths": [],
                                "risks": [],
                                "recommended_languages": [],
                                "missing_fields": [],
                            }
                        ),
                        "projects_json": as_json([]),
                        "review_notes": as_json(["PDF 已上传，系统正在异步解析。"]),
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                conn.execute(
                    text(
                        """
                        insert into resume.upload_jobs (
                          id, task_id, candidate_id, file_name, minio_bucket, minio_object_key,
                          status, progress, error, processing, created_at, updated_at
                        ) values (
                          :id, :task_id, :candidate_id, :file_name, :bucket, :object_key,
                          'queued', 0, null, cast(:processing as jsonb), :created_at, :updated_at
                        )
                        """
                    ),
                    {
                        "id": upload_id,
                        "task_id": task_id,
                        "candidate_id": candidate_id,
                        "file_name": filename,
                        "bucket": bucket,
                        "object_key": object_key,
                        "processing": as_json(processing),
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            created.append(
                {
                    "upload_id": upload_id,
                    "task_id": task_id,
                    "candidate_id": candidate_id,
                    "filename": filename,
                    "status": "queued",
                    "progress": 0,
                    "error": None,
                    "processing": processing,
                    "created_at": isoformat(now),
                    "updated_at": isoformat(now),
                }
            )
            Thread(target=self._parse_upload_async, args=(upload_id,), daemon=True).start()
        return {"items": created, "total": len(created)}

    def _parse_upload_async(self, upload_id: str) -> None:
        with db_connection(settings=self.settings) as conn:
            upload = conn.execute(
                text("select * from resume.upload_jobs where id = :id"),
                {"id": upload_id},
            ).mappings().first()
        if upload is None:
            return

        candidate_id = upload["candidate_id"]
        self._update_upload(
            upload_id,
            status="parsing",
            progress=35,
            processing=_build_processing(
                stage="parsing_pdf",
                status="running",
                progress=35,
                message="正在提取 PDF 文本层与页面结构。",
                step_statuses={"upload": "succeeded", "pdf_parse": "running"},
            ),
        )
        self._patch_candidate_processing(
            candidate_id,
            screening_status="解析中",
            processing=_build_processing(
                stage="parsing_pdf",
                status="running",
                progress=35,
                message="正在提取 PDF 文本层与页面结构。",
                step_statuses={"upload": "succeeded", "pdf_parse": "running"},
            ),
        )

        tmp_path: Path | None = None
        try:
            content = self.object_store.get_bytes(
                bucket=upload["minio_bucket"],
                object_key=upload["minio_object_key"],
            )
            with NamedTemporaryFile(prefix=f"{upload_id}-", suffix=".pdf", delete=False) as handle:
                handle.write(content)
                tmp_path = Path(handle.name)
            render_dir = tmp_path.parent / f"{upload_id}-render"
            profile = parse_resume_file(tmp_path, render_dir=render_dir)
            rendered_images = sorted(render_dir.glob("*.png")) if render_dir.exists() else []

            self._update_upload(
                upload_id,
                status="parsing",
                progress=72,
                processing=_build_processing(
                    stage="project_extract",
                    status="running",
                    progress=72,
                    message="文本层已提取，正在整理项目经历与出题焦点。",
                    step_statuses={
                        "upload": "succeeded",
                        "pdf_parse": "succeeded",
                        "project_extract": "running",
                    },
                ),
            )
            enrichment = enrich_resume_profile(profile, image_paths=rendered_images)

            page_metrics = profile.get("page_metrics", [])
            first_page_chars = page_metrics[0]["text_chars"] if page_metrics else 0
            multimodal_pages = sum(1 for item in page_metrics if item.get("needs_multimodal"))
            risks = enrichment.get("risks", [])
            quality = "高" if multimodal_pages <= 1 and not risks else "中"
            skills = list(enrichment.get("skills", []) or profile.get("skills", []))
            projects = deepcopy(enrichment.get("projects", []))
            analysis = {
                "focus_topics": deepcopy(enrichment.get("focus_topics", [])),
                "strengths": deepcopy(enrichment.get("strengths", [])),
                "risks": deepcopy(risks),
                "recommended_languages": deepcopy(enrichment.get("recommended_languages", [])),
                "missing_fields": deepcopy(enrichment.get("missing_fields", [])),
            }
            summary = enrichment.get("profile_summary") or (
                f"简历解析完成，已提取 {', '.join(skills) or '基础信息'} 等信号，建议生成考卷草稿。"
            )
            project_summary = enrichment.get("project_summary") or (
                (profile.get("raw_text", "") or "暂无项目摘要。").strip()[:160]
            )
            processing_done = _build_processing(
                stage="profile_ready",
                status="succeeded",
                progress=100,
                message="PDF 已完成解析，项目经历与出题焦点已整理完毕。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                },
            )
            review_notes = [
                "PDF 异步解析完成。",
                *([f"已识别 {len(projects)} 个项目卡片。"] if projects else []),
                (
                    "检测到低文本覆盖页，已触发多模态兜底。"
                    if multimodal_pages
                    else "文本层质量正常，未触发多模态兜底。"
                ),
            ]
            with db_connection(settings=self.settings) as conn:
                row = conn.execute(
                    text("select profile_json from resume.candidates where external_id = :id"),
                    {"id": candidate_id},
                ).mappings().first()
                profile_json = from_json(row["profile_json"] if row else {}, {})
                profile_json.update(
                    {
                        "summary": summary,
                        "project_summary": project_summary,
                        "parse_metrics": {
                            "first_page_characters": first_page_chars,
                            "multimodal_pages": multimodal_pages,
                            "confidence": quality,
                        },
                        "latest_upload_id": upload_id,
                    }
                )
                conn.execute(
                    text(
                        """
                        update resume.candidates set
                          name = :name,
                          email = :email,
                          phone = :phone,
                          city = coalesce(nullif(:city, ''), city),
                          screening_status = :screening_status,
                          status = 'ready',
                          quality = :quality,
                          skills = cast(:skills as jsonb),
                          profile_json = cast(:profile_json as jsonb),
                          analysis_json = cast(:analysis_json as jsonb),
                          projects_json = cast(:projects_json as jsonb),
                          review_notes = cast(:review_notes as jsonb),
                          updated_at = :updated_at
                        where external_id = :id
                        """
                    ),
                    {
                        "id": candidate_id,
                        "name": enrichment.get("display_name") or profile.get("name") or Path(upload["file_name"]).stem,
                        "email": enrichment.get("email") or profile.get("email"),
                        "phone": enrichment.get("phone"),
                        "city": enrichment.get("city") or "",
                        "screening_status": "待发卷",
                        "quality": quality,
                        "skills": as_json(skills),
                        "profile_json": as_json(profile_json),
                        "analysis_json": as_json(analysis),
                        "projects_json": as_json(projects),
                        "review_notes": as_json(review_notes),
                        "updated_at": datetime.now(UTC),
                    },
                )
                # stash processing in profile for read models
                profile_json["processing"] = processing_done
                conn.execute(
                    text(
                        """
                        update resume.candidates
                        set profile_json = cast(:profile_json as jsonb)
                        where external_id = :id
                        """
                    ),
                    {"id": candidate_id, "profile_json": as_json(profile_json)},
                )
            self._update_upload(
                upload_id,
                status="parsed",
                progress=100,
                processing=processing_done,
            )
        except Exception as exc:  # pragma: no cover
            failed = _build_processing(
                stage="failed",
                status="failed",
                progress=100,
                message="PDF 解析失败，请重新上传或人工处理。",
                step_statuses={"upload": "succeeded", "pdf_parse": "failed"},
                error_message=str(exc),
            )
            self._update_upload(
                upload_id,
                status="failed",
                progress=100,
                error=str(exc),
                processing=failed,
            )
            self._patch_candidate_processing(
                candidate_id,
                screening_status="解析失败",
                processing=failed,
                extra_review_note=f"解析失败：{exc}",
            )
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _update_upload(
        self,
        upload_id: str,
        *,
        status: str,
        progress: int,
        processing: dict[str, Any],
        error: str | None = None,
    ) -> None:
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    update resume.upload_jobs set
                      status = :status,
                      progress = :progress,
                      error = :error,
                      processing = cast(:processing as jsonb),
                      updated_at = :updated_at
                    where id = :id
                    """
                ),
                {
                    "id": upload_id,
                    "status": status,
                    "progress": progress,
                    "error": error,
                    "processing": as_json(processing),
                    "updated_at": datetime.now(UTC),
                },
            )

    def _patch_candidate_processing(
        self,
        candidate_id: str,
        *,
        screening_status: str,
        processing: dict[str, Any],
        extra_review_note: str | None = None,
    ) -> None:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text(
                    "select profile_json, review_notes from resume.candidates where external_id = :id"
                ),
                {"id": candidate_id},
            ).mappings().first()
            if row is None:
                return
            profile_json = from_json(row["profile_json"], {})
            profile_json["processing"] = processing
            notes = from_json(row["review_notes"], [])
            if extra_review_note:
                notes = list(notes) + [extra_review_note]
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      screening_status = :screening_status,
                      profile_json = cast(:profile_json as jsonb),
                      review_notes = cast(:review_notes as jsonb),
                      updated_at = :updated_at
                    where external_id = :id
                    """
                ),
                {
                    "id": candidate_id,
                    "screening_status": screening_status,
                    "profile_json": as_json(profile_json),
                    "review_notes": as_json(notes),
                    "updated_at": datetime.now(UTC),
                },
            )

    def get_upload(self, upload_id: str) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select * from resume.upload_jobs where id = :id"),
                {"id": upload_id},
            ).mappings().first()
        if row is None:
            raise LookupError("Upload not found.")
        return {
            "upload_id": row["id"],
            "task_id": row["task_id"],
            "candidate_id": row["candidate_id"],
            "filename": row["file_name"],
            "status": row["status"],
            "progress": row["progress"],
            "error": row["error"],
            "processing": from_json(row["processing"], {}),
            "created_at": isoformat(row["created_at"]),
            "updated_at": isoformat(row["updated_at"]),
        }

    def _load_candidate_row(self, candidate_id: str) -> Any:
        with db_connection(settings=self.settings) as conn:
            return conn.execute(
                text("select * from resume.candidates where external_id = :id"),
                {"id": candidate_id},
            ).mappings().first()

    def _serialize_candidate_card(self, row: Any) -> dict[str, Any]:
        profile = from_json(row["profile_json"], {})
        analysis = from_json(row["analysis_json"], {})
        processing = profile.get("processing")
        paper_id = row["paper_id"] or (
            (profile.get("paper_ids") or [None])[-1] if profile.get("paper_ids") else None
        )
        return {
            "id": row["external_id"],
            "task_id": row["task_id"],
            "name": row["name"] or "",
            "role": row["role"] or "",
            "city": row["city"] or "",
            "status": row["screening_status"] or row["status"] or "",
            "screening_status": row["screening_status"] or "",
            "quality": row["quality"] or "",
            "summary": profile.get("summary") or "",
            "skills": from_json(row["skills"], []),
            "resume_uploaded_at": isoformat(row["created_at"]),
            "resume_parse_status": "parsed" if row["screening_status"] not in {"解析中", "已上传简历"} else "queued",
            "risk_flag": "需核实" if analysis.get("risks") else "无",
            "risk_level": "medium" if analysis.get("risks") else "low",
            "risk_count": len(analysis.get("risks") or []),
            "paper_sent": bool(row["invitation_token"]),
            "paper_status": "published" if row["invitation_token"] else ("draft" if paper_id else "none"),
            "updated_at": isoformat(row["updated_at"]),
            "submitted_at": None,
            "next_action": self._next_action(row, paper_id),
            "paper_id": paper_id,
            "result_id": row["result_id"],
            "processing": processing,
        }

    def _next_action(self, row: Any, paper_id: str | None) -> dict[str, str]:
        cid = row["external_id"]
        status = row["screening_status"] or ""
        if row["result_id"] and status in {"已交卷", "评分复核中", "已完成筛选", "已淘汰", "已归档"}:
            return {"label": "查看结果", "target": f"/admin/results/{row['result_id']}"}
        if paper_id and status in {"待发卷", "待开考", "已发卷"}:
            return {"label": "编辑考卷", "target": f"/admin/papers/{paper_id}?candidateId={cid}"}
        if status == "拟出卷中":
            return {"label": "生成中", "target": f"/admin/candidates/{cid}"}
        if status in {"待审核", "待发卷", "信息整理中"} and not paper_id:
            return {"label": "生成考卷", "target": f"/admin/candidates/{cid}/papers/generate"}
        return {"label": "查看详情", "target": f"/admin/candidates/{cid}"}

    def list_candidates(
        self,
        *,
        task_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
        pending_review: bool | None = None,
        paper_sent: bool | None = None,
        paper_status: str | None = None,
        risk_level: str | None = None,
        keyword: str | None = None,
        sort_by: str | None = None,
        order: str | None = None,
    ) -> dict[str, Any]:
        clauses = ["external_id is not null"]
        params: dict[str, Any] = {}
        if task_id:
            clauses.append("task_id = :task_id")
            params["task_id"] = task_id
        if role:
            clauses.append("role ilike :role")
            params["role"] = f"%{role}%"
        if status:
            clauses.append("screening_status = :status")
            params["status"] = status
        if keyword:
            clauses.append("(name ilike :kw or role ilike :kw or city ilike :kw)")
            params["kw"] = f"%{keyword}%"
        if pending_review is True:
            clauses.append("screening_status = '待审核'")
        if paper_sent is True:
            clauses.append("invitation_token is not null")
        if paper_sent is False:
            clauses.append("invitation_token is null")

        sort_col = {
            "resume_uploaded_at": "created_at",
            "updated_at": "updated_at",
            "submitted_at": "updated_at",
        }.get(sort_by or "updated_at", "updated_at")
        sort_dir = "asc" if (order or "desc").lower() == "asc" else "desc"

        sql = f"""
            select * from resume.candidates
            where {' and '.join(clauses)}
            order by {sort_col} {sort_dir}
        """
        with db_connection(settings=self.settings) as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        items = [self._serialize_candidate_card(row) for row in rows]
        if paper_status:
            items = [item for item in items if item["paper_status"] == paper_status]
        if risk_level:
            items = [item for item in items if item["risk_level"] == risk_level]
        return {"items": items, "total": len(items)}

    def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        row = self._load_candidate_row(candidate_id)
        if row is None:
            raise LookupError("Candidate not found.")
        profile = from_json(row["profile_json"], {})
        analysis = from_json(row["analysis_json"], {})
        projects = from_json(row["projects_json"], [])
        paper_id = row["paper_id"] or (
            (profile.get("paper_ids") or [None])[-1] if profile.get("paper_ids") else None
        )
        has_pdf = bool(
            self._upload_object_for_candidate(candidate_id)
            or profile.get("latest_upload_id")
        )
        next_actions = []
        if paper_id:
            next_actions.append(
                {
                    "label": "编辑考卷",
                    "target": f"/admin/papers/{paper_id}?candidateId={candidate_id}",
                }
            )
        else:
            next_actions.append(
                {
                    "label": "生成考卷",
                    "target": f"/admin/candidates/{candidate_id}/papers/generate",
                }
            )
        next_actions.append(
            {"label": "修正候选人画像", "target": f"/admin/candidates/{candidate_id}/edit"}
        )
        return {
            "id": row["external_id"],
            "task_id": row["task_id"],
            "name": row["name"] or "",
            "role": row["role"] or "",
            "email": row["email"],
            "city": row["city"] or "",
            "phone": row["phone"] or "",
            "status": row["screening_status"] or "",
            "quality": row["quality"] or "",
            "skills": from_json(row["skills"], []),
            "hobbies": from_json(row["hobbies"], []),
            "height_cm": profile.get("height_cm"),
            "weight_kg": profile.get("weight_kg"),
            "available_in_days": profile.get("available_in_days"),
            "project_summary": profile.get("project_summary") or "",
            "projects": projects,
            "analysis": analysis,
            "processing": profile.get("processing"),
            "parse_metrics": profile.get("parse_metrics")
            or {"first_page_characters": 0, "multimodal_pages": 0, "confidence": ""},
            "review_notes": from_json(row["review_notes"], []),
            "paper_id": paper_id,
            "invitation_token": row["invitation_token"],
            "result_id": row["result_id"],
            "resume_pdf_url": f"/admin/candidates/{candidate_id}/resume.pdf" if has_pdf else None,
            "next_actions": next_actions,
        }

    def update_candidate(self, candidate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._load_candidate_row(candidate_id)
        if row is None:
            raise LookupError("Candidate not found.")
        profile = from_json(row["profile_json"], {})
        notes = from_json(row["review_notes"], [])
        if payload.get("project_summary") is not None:
            profile["project_summary"] = payload["project_summary"]
        for field in ("height_cm", "weight_kg", "available_in_days"):
            if field in payload and payload[field] is not None:
                profile[field] = payload[field]
        if payload.get("review_note"):
            notes = list(notes) + [payload["review_note"]]
        if payload.get("review_notes") is not None:
            notes = list(payload["review_notes"])

        name = payload["name"] if payload.get("name") is not None else row["name"]
        role = payload["role"] if payload.get("role") is not None else row["role"]
        email = payload["email"] if payload.get("email") is not None else row["email"]
        city = payload["city"] if payload.get("city") is not None else row["city"]
        phone = payload["phone"] if payload.get("phone") is not None else row["phone"]
        skills = payload["skills"] if payload.get("skills") is not None else from_json(row["skills"], [])
        hobbies = payload["hobbies"] if payload.get("hobbies") is not None else from_json(row["hobbies"], [])
        projects = (
            payload["projects"] if payload.get("projects") is not None else from_json(row["projects_json"], [])
        )

        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      name = :name,
                      role = :role,
                      email = :email,
                      city = :city,
                      phone = :phone,
                      skills = cast(:skills as jsonb),
                      hobbies = cast(:hobbies as jsonb),
                      projects_json = cast(:projects as jsonb),
                      profile_json = cast(:profile_json as jsonb),
                      review_notes = cast(:review_notes as jsonb),
                      updated_at = :updated_at
                    where external_id = :id
                    """
                ),
                {
                    "id": candidate_id,
                    "name": name,
                    "role": role,
                    "email": email,
                    "city": city,
                    "phone": phone,
                    "skills": as_json(skills),
                    "hobbies": as_json(hobbies),
                    "projects": as_json(projects),
                    "profile_json": as_json(profile),
                    "review_notes": as_json(notes),
                    "updated_at": datetime.now(UTC),
                },
            )
        return self.get_candidate(candidate_id)

    def _upload_object_for_candidate(self, candidate_id: str) -> dict[str, str] | None:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text(
                    """
                    select minio_bucket, minio_object_key, file_name
                    from resume.upload_jobs
                    where candidate_id = :cid
                      and minio_bucket is not null
                      and minio_object_key is not null
                    order by created_at desc
                    limit 1
                    """
                ),
                {"cid": candidate_id},
            ).mappings().first()
        if row is None:
            return None
        return {
            "bucket": row["minio_bucket"],
            "object_key": row["minio_object_key"],
            "file_name": row["file_name"],
        }

    def get_candidate_pdf_payload(self, candidate_id: str) -> dict[str, Any] | None:
        if self._load_candidate_row(candidate_id) is None:
            raise LookupError("Candidate not found.")
        obj = self._upload_object_for_candidate(candidate_id)
        if obj is None:
            return None
        content = self.object_store.get_bytes(bucket=obj["bucket"], object_key=obj["object_key"])
        return {"content": content, "filename": obj["file_name"] or f"{candidate_id}.pdf"}

    def get_dashboard(self) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            candidates = conn.execute(text("select * from resume.candidates where external_id is not null")).mappings().all()
        cards = [self._serialize_candidate_card(row) for row in candidates]
        screening = [c for c in cards if c["status"] in {"待审核", "解析中", "信息提取中", "信息整理中", "已上传简历"}]
        pending_publish = [c for c in cards if c["status"] == "待发卷"]
        exam_in_progress = [c for c in cards if c["status"] in {"已开考", "进行中考试"}]
        submitted = [c for c in cards if c["status"] in {"已交卷", "评分复核中"}]
        completed = [c for c in cards if c["status"] in {"已完成筛选", "已归档"}]
        return {
            "metrics": {
                "screening_candidate_count": len(screening),
                "pending_publish_count": len(pending_publish),
                "exam_in_progress_count": len(exam_in_progress),
                "submitted_count": len(submitted),
                "screening_completed_count": len(completed),
            },
            "screening_candidates": [
                {
                    "candidate_id": c["id"],
                    "name": c["name"],
                    "role": c["role"],
                    "status": c["status"],
                    "resume_uploaded_at": c["resume_uploaded_at"],
                    "target": f"/admin/candidates/{c['id']}",
                }
                for c in screening
            ],
            "pending_publish_candidates": [
                {
                    "candidate_id": c["id"],
                    "name": c["name"],
                    "role": c["role"],
                    "status": c["status"],
                    "target": f"/admin/candidates/{c['id']}",
                }
                for c in pending_publish
            ],
            "submitted_results": [],
        }
