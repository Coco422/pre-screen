"""Postgres-backed exam papers, invitations, sessions, results, and risk events."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import randbelow, token_urlsafe
from threading import Thread
from typing import Any

from sqlalchemy import text

from pre_screen_common.db import db_connection
from pre_screen_common.settings import AppSettings, get_settings
from services.exam.app.domain.paper_generator import generate_paper_draft
from services.gateway.app.domain.demo_store import (
    AUTOSAVE_INTERVAL_MS,
    HEARTBEAT_INTERVAL_MS,
    RISK_EVENT_TYPES,
    _build_processing,
    gateway_demo_store,
)
from services.gateway.app.domain.resume_intelligence import build_question_brief
from services.gateway.app.repositories.candidate_repository import CandidateRepository
from services.gateway.app.repositories.ids import next_text_id
from services.gateway.app.repositories.json_util import as_json, from_json, isoformat
from services.scoring.app.domain.objective import score_objective_answer
from services.scoring.app.domain.subjective import suggest_subjective_score
from services.scoring.app.domain.summary import build_score_summary


class ExamRepository:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings

    @property
    def settings(self) -> AppSettings:
        return self._settings or get_settings()

    # --- Papers ---

    def generate_paper(self, candidate_id: str) -> dict[str, Any]:
        cand = CandidateRepository(settings=self.settings).get_candidate(candidate_id)
        profile = self._load_candidate_profile_row(candidate_id)
        processing = (profile.get("processing") or {}) if profile else {}
        if processing.get("stage") == "paper_generate" and processing.get("status") in {
            "queued",
            "running",
        }:
            return {
                "candidate_id": candidate_id,
                "status": "generating",
                "paper_id": cand.get("paper_id"),
                "processing": processing,
                "message": "考卷生成进行中",
            }
        if cand.get("paper_id"):
            paper = self.get_paper(cand["paper_id"])
            return {
                "candidate_id": candidate_id,
                "status": "ready",
                "paper_id": paper["paper_id"],
                "processing": processing,
                "message": "已有考卷草稿",
                "paper": paper,
            }

        self._set_candidate_paper_state(
            candidate_id,
            screening_status="拟出卷中",
            processing=_build_processing(
                stage="paper_generate",
                status="running",
                progress=12,
                message="考卷生成已入队，正在结合简历与 JD 出题…",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "running",
                },
            ),
        )
        Thread(target=self._generate_paper_async, args=(candidate_id,), daemon=True).start()
        return {
            "candidate_id": candidate_id,
            "status": "generating",
            "paper_id": None,
            "processing": self._load_candidate_profile_row(candidate_id).get("processing"),
            "message": "考卷生成已入队",
        }

    def _generate_paper_async(self, candidate_id: str) -> None:
        try:
            cand = CandidateRepository(settings=self.settings).get_candidate(candidate_id)
            with db_connection(settings=self.settings) as conn:
                task = conn.execute(
                    text("select * from app.screening_tasks where id = :id"),
                    {"id": cand["task_id"]},
                ).mappings().first()
            if task is None:
                raise LookupError("Task not found.")
            template_config = from_json(task["template_config"], {})
            tags = from_json(task["tags"], [])
            candidate_snapshot = {
                "skills": cand.get("skills") or [],
                "projects": cand.get("projects") or [],
                "focus_topics": (cand.get("analysis") or {}).get("focus_topics", []),
                "recommended_languages": (cand.get("analysis") or {}).get(
                    "recommended_languages", []
                ),
                "project_summary": cand.get("project_summary") or "",
            }
            self._set_candidate_paper_state(
                candidate_id,
                screening_status="拟出卷中",
                processing=_build_processing(
                    stage="paper_generate",
                    status="running",
                    progress=40,
                    message="正在调用模型生成针对性题目…",
                    step_statuses={
                        "upload": "succeeded",
                        "pdf_parse": "succeeded",
                        "project_extract": "succeeded",
                        "paper_generate": "running",
                    },
                ),
            )
            question_brief = build_question_brief(
                candidate_profile=candidate_snapshot,
                job_context={
                    "title": task["title"],
                    "department": task["department"],
                    "jd_text": task["jd_text"],
                    "tags": tags,
                },
            )
            draft = generate_paper_draft(
                job_template={"name": task["title"], **template_config, "tags": tags},
                jd_text=task["jd_text"],
                candidate_profile={**candidate_snapshot, "question_brief": question_brief},
            )
            paper_id = next_text_id("paper", "p", settings=self.settings)
            questions = [
                gateway_demo_store._materialize_question(item) for item in draft["questions"]
            ]
            now = datetime.now(UTC)
            with db_connection(settings=self.settings) as conn:
                conn.execute(
                    text(
                        """
                        insert into exam.papers (
                          id, candidate_id, task_id, title, duration_minutes, status,
                          introduction, questions, mix, generation_summary, created_at, updated_at
                        ) values (
                          :id, :candidate_id, :task_id, :title, :duration_minutes, 'draft',
                          :introduction, cast(:questions as jsonb), cast(:mix as jsonb),
                          cast(:generation_summary as jsonb), :created_at, :updated_at
                        )
                        """
                    ),
                    {
                        "id": paper_id,
                        "candidate_id": candidate_id,
                        "task_id": cand["task_id"],
                        "title": f"{task['title']}在线测评草稿",
                        "duration_minutes": int(task["duration_minutes"] or 90),
                        "introduction": draft.get("introduction")
                        or "请先完成基础信息，再依次完成客观题、主观题和代码题。",
                        "questions": as_json(questions),
                        "mix": as_json(draft.get("question_mix") or {}),
                        "generation_summary": as_json(draft.get("generation_summary") or {}),
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            profile = self._load_candidate_profile_row(candidate_id) or {}
            paper_ids = list(profile.get("paper_ids") or [])
            paper_ids.append(paper_id)
            profile["paper_ids"] = paper_ids
            profile["summary"] = "考卷草稿已生成，可进入编辑与发布。"
            profile["processing"] = _build_processing(
                stage="paper_ready",
                status="succeeded",
                progress=100,
                message="考卷草稿已生成，可编辑后发布考试链接。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "succeeded",
                },
            )
            with db_connection(settings=self.settings) as conn:
                conn.execute(
                    text(
                        """
                        update resume.candidates set
                          paper_id = :paper_id,
                          screening_status = '待发卷',
                          profile_json = cast(:profile_json as jsonb),
                          updated_at = :updated_at
                        where external_id = :id
                        """
                    ),
                    {
                        "id": candidate_id,
                        "paper_id": paper_id,
                        "profile_json": as_json(profile),
                        "updated_at": datetime.now(UTC),
                    },
                )
        except Exception as exc:
            self._set_candidate_paper_state(
                candidate_id,
                screening_status="待发卷",
                processing=_build_processing(
                    stage="paper_generate",
                    status="failed",
                    progress=100,
                    message=f"考卷生成失败：{exc}",
                    error_message=str(exc),
                    step_statuses={
                        "upload": "succeeded",
                        "pdf_parse": "succeeded",
                        "project_extract": "succeeded",
                        "paper_generate": "failed",
                    },
                ),
            )

    def _load_candidate_profile_row(self, candidate_id: str) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select profile_json from resume.candidates where external_id = :id"),
                {"id": candidate_id},
            ).mappings().first()
        if row is None:
            return {}
        return from_json(row["profile_json"], {})

    def _set_candidate_paper_state(
        self,
        candidate_id: str,
        *,
        screening_status: str,
        processing: dict[str, Any],
    ) -> None:
        profile = self._load_candidate_profile_row(candidate_id)
        profile["processing"] = processing
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      screening_status = :status,
                      profile_json = cast(:profile as jsonb),
                      updated_at = :updated_at
                    where external_id = :id
                    """
                ),
                {
                    "id": candidate_id,
                    "status": screening_status,
                    "profile": as_json(profile),
                    "updated_at": datetime.now(UTC),
                },
            )

    def list_papers(self, *, status: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        clauses = ["1=1"]
        params: dict[str, Any] = {}
        if status:
            clauses.append("p.status = :status")
            params["status"] = status
        if task_id:
            clauses.append("p.task_id = :task_id")
            params["task_id"] = task_id
        sql = f"""
            select p.*, c.name as candidate_name
            from exam.papers p
            left join resume.candidates c on c.external_id = p.candidate_id
            where {' and '.join(clauses)}
            order by p.updated_at desc
        """
        with db_connection(settings=self.settings) as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        items = [
            {
                "paper_id": row["id"],
                "candidate_id": row["candidate_id"],
                "candidate_name": row["candidate_name"] or row["candidate_id"],
                "task_id": row["task_id"],
                "title": row["title"],
                "status": row["status"],
                "duration_minutes": row["duration_minutes"],
                "question_count": len(from_json(row["questions"], [])),
                "updated_at": isoformat(row["updated_at"]),
                "created_at": isoformat(row["created_at"]),
            }
            for row in rows
        ]
        return {"items": items, "total": len(items)}

    def get_paper(self, paper_id: str) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select * from exam.papers where id = :id"),
                {"id": paper_id},
            ).mappings().first()
            inv = conn.execute(
                text(
                    """
                    select * from exam.invitations
                    where paper_id = :paper_id
                    order by created_at desc
                    limit 1
                    """
                ),
                {"paper_id": paper_id},
            ).mappings().first()
        if row is None:
            raise LookupError("Paper draft not found.")
        invitation = None
        if inv is not None:
            invitation = {
                "token": inv["access_token"],
                "verify_code": inv["verify_code_plain"] or "",
                "start_url": f"/exam/{inv['access_token']}",
                "status": inv["status"],
            }
        return {
            "paper_id": row["id"],
            "candidate_id": row["candidate_id"],
            "task_id": row["task_id"],
            "title": row["title"],
            "mix": from_json(row["mix"], {}),
            "status": row["status"],
            "duration_minutes": row["duration_minutes"],
            "introduction": row["introduction"]
            or "请先完成基础信息，再依次完成客观题、主观题和代码题。",
            "questions": from_json(row["questions"], []),
            "generation_summary": from_json(row["generation_summary"], {}),
            "invitation": invitation,
            "updated_at": isoformat(row["updated_at"]),
        }

    def update_paper(self, paper_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        paper = self.get_paper(paper_id)
        questions = deepcopy(paper["questions"])
        if payload.get("questions") is not None:
            updates = {item["id"]: item for item in payload["questions"] if item.get("id")}
            for question in questions:
                patch = updates.get(question["id"])
                if patch is None:
                    continue
                for field in (
                    "title",
                    "description",
                    "score",
                    "rubric_text",
                    "language",
                    "starter_code",
                ):
                    if patch.get(field) is not None:
                        question[field] = patch[field]
                for field in ("fields", "options", "answer_key", "supported_languages"):
                    if patch.get(field) is not None:
                        question[field] = deepcopy(patch[field])
        title = payload["title"] if payload.get("title") is not None else paper["title"]
        duration = (
            payload["duration_minutes"]
            if payload.get("duration_minutes") is not None
            else paper["duration_minutes"]
        )
        introduction = (
            payload["introduction"]
            if payload.get("introduction") is not None
            else paper["introduction"]
        )
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    update exam.papers set
                      title = :title,
                      duration_minutes = :duration_minutes,
                      introduction = :introduction,
                      questions = cast(:questions as jsonb),
                      updated_at = :updated_at
                    where id = :id
                    """
                ),
                {
                    "id": paper_id,
                    "title": title,
                    "duration_minutes": duration,
                    "introduction": introduction,
                    "questions": as_json(questions),
                    "updated_at": datetime.now(UTC),
                },
            )
        return self.get_paper(paper_id)

    def publish_paper(self, paper_id: str, duration_minutes: int | None = None) -> dict[str, Any]:
        paper = self.get_paper(paper_id)
        token = token_urlsafe(16)
        verification_code = f"{randbelow(1_000_000):06d}"
        invitation_id = next_text_id("invitation", "i", settings=self.settings)
        duration = duration_minutes or paper["duration_minutes"]
        now = datetime.now(UTC)
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    insert into exam.invitations (
                      id, paper_id, access_token, one_time_code_hash, verify_code_plain,
                      duration_minutes, status, created_at
                    ) values (
                      :id, :paper_id, :token, :code_hash, :code_plain,
                      :duration_minutes, 'ready', :created_at
                    )
                    """
                ),
                {
                    "id": invitation_id,
                    "paper_id": paper_id,
                    "token": token,
                    "code_hash": sha256(verification_code.encode("utf-8")).hexdigest(),
                    "code_plain": verification_code,
                    "duration_minutes": duration,
                    "created_at": now,
                },
            )
            conn.execute(
                text(
                    """
                    update exam.papers set status = 'published', updated_at = :updated_at
                    where id = :id
                    """
                ),
                {"id": paper_id, "updated_at": now},
            )
            profile = self._load_candidate_profile_row(paper["candidate_id"])
            profile["processing"] = _build_processing(
                stage="published",
                status="succeeded",
                progress=100,
                message="考试入口已发布，可直接复制链接与验证码给候选人。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "succeeded",
                    "paper_publish": "succeeded",
                },
            )
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      screening_status = '待开考',
                      invitation_token = :token,
                      paper_id = :paper_id,
                      profile_json = cast(:profile as jsonb),
                      updated_at = :updated_at
                    where external_id = :cid
                    """
                ),
                {
                    "cid": paper["candidate_id"],
                    "token": token,
                    "paper_id": paper_id,
                    "profile": as_json(profile),
                    "updated_at": now,
                },
            )
        return {
            "paper_id": paper_id,
            "token": token,
            "verification_code": verification_code,
            "exam_url": f"/exam/{token}",
            "access_state": "not_started",
            "duration_minutes": duration,
        }

    # --- Exam public path ---

    def _load_invitation(self, token: str) -> Any:
        with db_connection(settings=self.settings) as conn:
            return conn.execute(
                text("select * from exam.invitations where access_token = :token"),
                {"token": token},
            ).mappings().first()

    def _load_session_by_token(self, token: str) -> Any:
        with db_connection(settings=self.settings) as conn:
            return conn.execute(
                text(
                    """
                    select * from exam.sessions
                    where access_token = :token
                    order by created_at desc
                    limit 1
                    """
                ),
                {"token": token},
            ).mappings().first()

    def get_exam_payload(self, token: str) -> dict[str, Any]:
        inv = self._load_invitation(token)
        if inv is None:
            raise LookupError("Exam token not found.")
        paper = self.get_paper(inv["paper_id"])
        try:
            candidate = CandidateRepository(settings=self.settings).get_candidate(paper["candidate_id"])
            candidate_name = candidate.get("name") or paper["candidate_id"]
        except LookupError:
            candidate_name = paper["candidate_id"]
        session = self._load_session_by_token(token)
        access_state = "not_started"
        if session is not None:
            if session["status"] in {"completed", "submitted"}:
                access_state = "submitted"
            else:
                access_state = "in_progress"
        answers = from_json(session["answers"], {}) if session else {}
        payload: dict[str, Any] = {
            "token": token,
            "state": access_state,
            "access_state": access_state,
            "paper_title": paper["title"],
            "candidate_name": candidate_name,
            "duration_minutes": inv["duration_minutes"],
            "heartbeat_interval_ms": HEARTBEAT_INTERVAL_MS,
            "autosave_interval_ms": AUTOSAVE_INTERVAL_MS,
            "risk_events": deepcopy(RISK_EVENT_TYPES),
            "instructions": [
                "请输入验证码进入考试。",
                "系统会自动保存答案，并记录基础风控事件。",
                "交卷后 HR 将查看评分与作答详情。",
            ],
            "started_at": isoformat(session["started_at"]) if session else None,
            "expires_at": isoformat(session["expires_at"]) if session else None,
            "submitted_at": isoformat(session["submitted_at"]) if session else None,
            "last_heartbeat_at": isoformat(session["last_heartbeat_at"]) if session else None,
            "answers": {
                qid: deepcopy(item.get("draft_answer", {})) for qid, item in answers.items()
            },
            "submission_summary": None,
            "questions": [],
        }
        if access_state != "not_started":
            payload["questions"] = [
                self._serialize_public_question(q) for q in paper["questions"]
            ]
        if session is not None:
            # result_id stored in coding_submissions meta or we query scoring
            with db_connection(settings=self.settings) as conn:
                result = conn.execute(
                    text(
                        """
                        select * from scoring.results
                        where session_id = :sid
                        order by submitted_at desc
                        limit 1
                        """
                    ),
                    {"sid": session["id"]},
                ).mappings().first()
            if result is not None:
                summary = from_json(result["summary"], {})
                payload["result_id"] = result["id"]
                payload["submission_summary"] = {
                    "submitted_at": isoformat(result["submitted_at"]),
                    "total_score": summary.get("total_score", 0),
                    "objective_score": summary.get("objective_score", 0),
                    "subjective_score": summary.get("subjective_score", 0),
                    "coding_score": summary.get("coding_score", 0),
                }
        return payload

    def start_exam(self, token: str, verification_code: str) -> dict[str, Any]:
        inv = self._load_invitation(token)
        if inv is None:
            raise LookupError("Exam token not found.")
        if inv["one_time_code_hash"] != sha256(verification_code.encode("utf-8")).hexdigest():
            raise PermissionError("Verification code is invalid.")
        existing = self._load_session_by_token(token)
        if existing is not None:
            return self._serialize_session(existing)
        paper = self.get_paper(inv["paper_id"])
        session_id = next_text_id("session", "s", settings=self.settings)
        start_at = datetime.now(UTC)
        expires_at = start_at + timedelta(minutes=int(inv["duration_minutes"] or 90))
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    insert into exam.sessions (
                      id, invitation_id, paper_id, candidate_id, access_token, status,
                      started_at, expires_at, submitted_at, last_heartbeat_at,
                      answers, risk_events, coding_submissions, created_at
                    ) values (
                      :id, :invitation_id, :paper_id, :candidate_id, :token, 'in_progress',
                      :started_at, :expires_at, null, :last_heartbeat_at,
                      cast(:answers as jsonb), cast(:risk_events as jsonb),
                      cast(:coding_submissions as jsonb), :created_at
                    )
                    """
                ),
                {
                    "id": session_id,
                    "invitation_id": inv["id"],
                    "paper_id": inv["paper_id"],
                    "candidate_id": paper["candidate_id"],
                    "token": token,
                    "started_at": start_at,
                    "expires_at": expires_at,
                    "last_heartbeat_at": start_at,
                    "answers": as_json({}),
                    "risk_events": as_json([]),
                    "coding_submissions": as_json({}),
                    "created_at": start_at,
                },
            )
            conn.execute(
                text(
                    """
                    update exam.invitations set status = 'in_progress' where id = :id
                    """
                ),
                {"id": inv["id"]},
            )
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      screening_status = '已开考',
                      updated_at = :updated_at
                    where external_id = :cid
                    """
                ),
                {"cid": paper["candidate_id"], "updated_at": start_at},
            )
        session = self._load_session_by_token(token)
        return self._serialize_session(session)

    def _require_active_session(self, token: str) -> Any:
        inv = self._load_invitation(token)
        if inv is None:
            raise LookupError("Exam token not found.")
        session = self._load_session_by_token(token)
        if session is None:
            raise ValueError("Exam has not started.")
        if session["status"] not in {"in_progress"}:
            raise ValueError("Exam session is not active.")
        return session

    def heartbeat(self, token: str) -> dict[str, Any]:
        session = self._require_active_session(token)
        now = datetime.now(UTC)
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    "update exam.sessions set last_heartbeat_at = :ts where id = :id"
                ),
                {"id": session["id"], "ts": now},
            )
        return {
            "token": token,
            "last_heartbeat_at": isoformat(now),
            "status": "accepted",
        }

    def save_answer(self, token: str, question_id: str, draft_answer: dict[str, Any]) -> dict[str, Any]:
        session = self._require_active_session(token)
        paper = self.get_paper(session["paper_id"])
        if not any(q["id"] == question_id for q in paper["questions"]):
            raise LookupError("Question not found.")
        answers = from_json(session["answers"], {})
        now = datetime.now(UTC)
        existing = answers.get(question_id) or {}
        entry: dict[str, Any] = {
            "draft_answer": deepcopy(draft_answer),
            "last_saved_at": isoformat(now),
            "status": "saved",
        }
        if existing.get("coding_submission") is not None:
            entry["coding_submission"] = existing["coding_submission"]
        answers[question_id] = entry
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text("update exam.sessions set answers = cast(:answers as jsonb) where id = :id"),
                {"id": session["id"], "answers": as_json(answers)},
            )
            conn.execute(
                text(
                    """
                    insert into exam.answer_drafts (session_id, question_id, draft_answer, updated_at)
                    values (:sid, :qid, cast(:draft as jsonb), :updated_at)
                    on conflict (session_id, question_id) do update set
                      draft_answer = excluded.draft_answer,
                      updated_at = excluded.updated_at
                    """
                ),
                {
                    "sid": session["id"],
                    "qid": question_id,
                    "draft": as_json(draft_answer),
                    "updated_at": now,
                },
            )
        return {
            "token": token,
            "question_id": question_id,
            "draft_answer": deepcopy(draft_answer),
            "last_saved_at": isoformat(now),
            "status": "saved",
        }

    def record_risk_event(self, token: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._require_active_session(token)
        now = datetime.now(UTC)
        events = from_json(session["risk_events"], [])
        event = {"event_type": event_type, "payload": deepcopy(payload), "created_at": isoformat(now)}
        events.append(event)
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    "update exam.sessions set risk_events = cast(:events as jsonb) where id = :id"
                ),
                {"id": session["id"], "events": as_json(events)},
            )
            conn.execute(
                text(
                    """
                    insert into risk.events (session_id, event_type, payload, created_at)
                    values (:sid, :etype, cast(:payload as jsonb), :created_at)
                    """
                ),
                {
                    "sid": session["id"],
                    "etype": event_type,
                    "payload": as_json(payload),
                    "created_at": now,
                },
            )
        return {
            "token": token,
            "event_type": event_type,
            "payload": deepcopy(payload),
            "created_at": isoformat(now),
        }

    def get_coding_question(self, token: str, question_id: str) -> dict[str, Any]:
        session = self._require_active_session(token)
        paper = self.get_paper(session["paper_id"])
        for question in paper["questions"]:
            if question["id"] == question_id and question["kind"] == "coding":
                return deepcopy(question)
        raise ValueError("Coding question not found.")

    def store_coding_submission(
        self,
        token: str,
        question_id: str,
        *,
        language: str,
        source_code: str,
        result: dict[str, Any],
    ) -> None:
        session = self._require_active_session(token)
        answers = from_json(session["answers"], {})
        now = datetime.now(UTC)
        answer = answers.setdefault(question_id, {})
        answer["draft_answer"] = {"language": language, "source_code": source_code}
        answer["coding_submission"] = deepcopy(result)
        answer["last_saved_at"] = isoformat(now)
        answer["status"] = "saved"
        coding = from_json(session["coding_submissions"], {})
        coding[question_id] = deepcopy(result)
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    update exam.sessions set
                      answers = cast(:answers as jsonb),
                      coding_submissions = cast(:coding as jsonb)
                    where id = :id
                    """
                ),
                {
                    "id": session["id"],
                    "answers": as_json(answers),
                    "coding": as_json(coding),
                },
            )
            conn.execute(
                text(
                    """
                    insert into judge.submissions (
                      session_id, question_id, mode, language, source_code, result_json, created_at
                    ) values (
                      :sid, :qid, 'submit', :language, :source_code, cast(:result as jsonb), :created_at
                    )
                    """
                ),
                {
                    "sid": session["id"],
                    "qid": question_id,
                    "language": language,
                    "source_code": source_code,
                    "result": as_json(result),
                    "created_at": now,
                },
            )

    def submit_exam(self, token: str) -> dict[str, Any]:
        session = self._require_active_session(token)
        inv = self._load_invitation(token)
        paper = self.get_paper(session["paper_id"])
        answers = from_json(session["answers"], {})
        risk_events = from_json(session["risk_events"], [])
        objective_score = 0
        subjective_score = 0
        coding_score = 0
        reviews: list[dict[str, Any]] = []
        for question in paper["questions"]:
            answer = answers.get(question["id"], {})
            draft_answer = deepcopy(answer.get("draft_answer", {}))
            review: dict[str, Any] = {
                "question_id": question["id"],
                "kind": question["kind"],
                "title": question["title"],
                "max_score": question["score"],
                "draft_answer": draft_answer,
            }
            if question["kind"] == "objective":
                score = score_objective_answer(
                    answer=draft_answer.get("answer", ""),
                    answer_key=question.get("answer_key"),
                    full_score=question["score"],
                    mode=question.get("mode") or "single_select",
                )
                objective_score += score
                review["score"] = score
                review["result"] = "passed" if score else "failed"
            elif question["kind"] == "subjective":
                suggestion = suggest_subjective_score(
                    answer_text=draft_answer.get("answer_text", ""),
                    rubric_text=question.get("rubric_text") or "",
                    max_score=question["score"],
                )
                subjective_score += suggestion["suggested_score"]
                review["score"] = suggestion["suggested_score"]
                review["reasoning_summary"] = suggestion["reasoning_summary"]
            elif question["kind"] == "coding":
                submission = answer.get("coding_submission")
                score = submission["summary"]["total_score"] if submission else 0
                coding_score += score
                review["score"] = score
                review["results"] = deepcopy(submission["results"]) if submission else []
            else:
                review["score"] = 0
            reviews.append(review)

        risk_summary = {
            "event_count": len(risk_events),
            "event_types": dict(Counter(event["event_type"] for event in risk_events)),
        }
        summary = build_score_summary(
            objective_score=objective_score,
            subjective_score=subjective_score,
            coding_score=coding_score,
            risk_summary=risk_summary,
        )
        result_id = next_text_id("result", "r", settings=self.settings)
        submitted_at = datetime.now(UTC)
        with db_connection(settings=self.settings) as conn:
            conn.execute(
                text(
                    """
                    insert into scoring.results (
                      id, session_id, candidate_id, paper_id, task_id, status, review_status,
                      screening_decision, summary, question_reviews, risk_events, review_notes,
                      submitted_at, created_at
                    ) values (
                      :id, :session_id, :candidate_id, :paper_id, :task_id, 'completed', 'pending',
                      null, cast(:summary as jsonb), cast(:reviews as jsonb),
                      cast(:risk_events as jsonb), cast(:notes as jsonb),
                      :submitted_at, :created_at
                    )
                    """
                ),
                {
                    "id": result_id,
                    "session_id": session["id"],
                    "candidate_id": session["candidate_id"],
                    "paper_id": session["paper_id"],
                    "task_id": paper.get("task_id"),
                    "summary": as_json(summary),
                    "reviews": as_json(reviews),
                    "risk_events": as_json(risk_events),
                    "notes": as_json([]),
                    "submitted_at": submitted_at,
                    "created_at": submitted_at,
                },
            )
            conn.execute(
                text(
                    """
                    update exam.sessions set
                      status = 'completed',
                      submitted_at = :submitted_at
                    where id = :id
                    """
                ),
                {"id": session["id"], "submitted_at": submitted_at},
            )
            if inv is not None:
                conn.execute(
                    text("update exam.invitations set status = 'submitted' where id = :id"),
                    {"id": inv["id"]},
                )
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      screening_status = '已交卷',
                      result_id = :result_id,
                      updated_at = :updated_at
                    where external_id = :cid
                    """
                ),
                {
                    "cid": session["candidate_id"],
                    "result_id": result_id,
                    "updated_at": submitted_at,
                },
            )
        return {
            "result_id": result_id,
            "session_id": session["id"],
            "status": "completed",
            "summary": deepcopy(summary),
            "submitted_at": isoformat(submitted_at),
        }

    def list_results(self, *, status: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        clauses = ["1=1"]
        params: dict[str, Any] = {}
        if status:
            clauses.append("r.status = :status")
            params["status"] = status
        if task_id:
            clauses.append("r.task_id = :task_id")
            params["task_id"] = task_id
        sql = f"""
            select r.*, c.name as candidate_name, c.role as candidate_role, p.title as paper_title
            from scoring.results r
            left join resume.candidates c on c.external_id = r.candidate_id
            left join exam.papers p on p.id = r.paper_id
            where {' and '.join(clauses)}
            order by r.submitted_at desc nulls last
        """
        with db_connection(settings=self.settings) as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        items = []
        for row in rows:
            summary = from_json(row["summary"], {})
            items.append(
                {
                    "result_id": row["id"],
                    "session_id": row["session_id"],
                    "candidate_id": row["candidate_id"],
                    "candidate_name": row["candidate_name"] or row["candidate_id"],
                    "role": row["candidate_role"] or "",
                    "paper_id": row["paper_id"],
                    "paper_title": row["paper_title"] or "",
                    "task_id": row["task_id"],
                    "status": row["status"],
                    "review_status": row["review_status"] or "pending",
                    "screening_decision": row["screening_decision"],
                    "total_score": summary.get("total_score", 0),
                    "submitted_at": isoformat(row["submitted_at"]),
                }
            )
        return {"items": items, "total": len(items)}

    def get_result(self, result_id: str) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select * from scoring.results where id = :id"),
                {"id": result_id},
            ).mappings().first()
        if row is None:
            raise LookupError("Result not found.")
        paper = self.get_paper(row["paper_id"])
        try:
            candidate = CandidateRepository(settings=self.settings).get_candidate(row["candidate_id"])
        except LookupError:
            candidate = {"id": row["candidate_id"], "name": row["candidate_id"], "role": ""}
        risk_events = from_json(row["risk_events"], [])
        return {
            "result_id": row["id"],
            "session_id": row["session_id"],
            "status": row["status"],
            "review_status": row["review_status"] or "pending",
            "review_notes": from_json(row["review_notes"], []),
            "screening_status": row["screening_decision"],
            "submitted_at": isoformat(row["submitted_at"]),
            "candidate": candidate,
            "paper": paper,
            "summary": from_json(row["summary"], {}),
            "answers": from_json(row["question_reviews"], []),
            "risk_events": risk_events,
        }

    def review_result(self, result_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select * from scoring.results where id = :id"),
                {"id": result_id},
            ).mappings().first()
            if row is None:
                raise LookupError("Result not found.")
            summary = from_json(row["summary"], {})
            notes = from_json(row["review_notes"], [])
            if payload.get("final_subjective_score") is not None:
                summary["subjective_score"] = payload["final_subjective_score"]
                summary["total_score"] = (
                    int(summary.get("objective_score") or 0)
                    + int(payload["final_subjective_score"])
                    + int(summary.get("coding_score") or 0)
                )
            if payload.get("review_notes") is not None:
                notes = list(notes) + list(payload["review_notes"])
            risk_override = payload.get("risk_override")
            conn.execute(
                text(
                    """
                    update scoring.results set
                      summary = cast(:summary as jsonb),
                      review_notes = cast(:notes as jsonb),
                      review_status = 'reviewed',
                      risk_override = coalesce(:risk_override, risk_override),
                      reviewed_at = :reviewed_at
                    where id = :id
                    """
                ),
                {
                    "id": result_id,
                    "summary": as_json(summary),
                    "notes": as_json(notes),
                    "risk_override": risk_override,
                    "reviewed_at": datetime.now(UTC),
                },
            )
        return self.get_result(result_id)

    def complete_screening(self, result_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        decision = payload["decision"]
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select * from scoring.results where id = :id"),
                {"id": result_id},
            ).mappings().first()
            if row is None:
                raise LookupError("Result not found.")
            notes = from_json(row["review_notes"], [])
            if payload.get("review_notes"):
                notes = list(notes) + list(payload["review_notes"])
            now = datetime.now(UTC)
            conn.execute(
                text(
                    """
                    update scoring.results set
                      screening_decision = :decision,
                      review_notes = cast(:notes as jsonb),
                      status = 'completed',
                      completed_at = :completed_at
                    where id = :id
                    """
                ),
                {
                    "id": result_id,
                    "decision": decision,
                    "notes": as_json(notes),
                    "completed_at": now,
                },
            )
            candidate_status = "已完成筛选" if decision == "pass" else "已淘汰"
            conn.execute(
                text(
                    """
                    update resume.candidates set
                      screening_status = :status,
                      updated_at = :updated_at
                    where external_id = :cid
                    """
                ),
                {
                    "cid": row["candidate_id"],
                    "status": candidate_status,
                    "updated_at": now,
                },
            )
        return {
            "result_id": result_id,
            "candidate_id": row["candidate_id"],
            "decision": decision,
            "completed_at": isoformat(datetime.now(UTC)),
        }

    def list_monitor_sessions(self) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            rows = conn.execute(
                text(
                    """
                    select s.*, c.name as candidate_name, p.title as paper_title, p.questions
                    from exam.sessions s
                    left join resume.candidates c on c.external_id = s.candidate_id
                    left join exam.papers p on p.id = s.paper_id
                    where s.status = 'in_progress'
                    order by s.started_at desc
                    """
                )
            ).mappings().all()
        items = []
        for row in rows:
            answers = from_json(row["answers"], {})
            questions = from_json(row["questions"], []) if row["questions"] is not None else []
            risk_events = from_json(row["risk_events"], [])
            items.append(
                {
                    "session_id": row["id"],
                    "candidate_name": row["candidate_name"] or row["candidate_id"],
                    "paper_title": row["paper_title"] or row["paper_id"],
                    "status": row["status"],
                    "started_at": isoformat(row["started_at"]),
                    "expires_at": isoformat(row["expires_at"]),
                    "answered_count": len(answers),
                    "total_questions": len(questions),
                    "last_heartbeat_at": isoformat(row["last_heartbeat_at"]),
                    "risk_event_count": len(risk_events),
                }
            )
        return {"items": items, "total": len(items)}

    def force_submit_session(self, session_id: str) -> dict[str, Any]:
        with db_connection(settings=self.settings) as conn:
            row = conn.execute(
                text("select * from exam.sessions where id = :id"),
                {"id": session_id},
            ).mappings().first()
        if row is None:
            raise LookupError("Session not found.")
        if row["status"] != "in_progress":
            raise ValueError("Session is not active.")
        result = self.submit_exam(row["access_token"])
        return {
            "session_id": session_id,
            "submitted_at": result["submitted_at"],
            "status": "submitted",
        }

    def _serialize_session(self, session: Any) -> dict[str, Any]:
        return {
            "session_id": session["id"],
            "token": session["access_token"],
            "paper_id": session["paper_id"],
            "candidate_id": session["candidate_id"],
            "status": session["status"],
            "started_at": isoformat(session["started_at"]),
            "expires_at": isoformat(session["expires_at"]),
            "submitted_at": isoformat(session["submitted_at"]),
            "last_heartbeat_at": isoformat(session["last_heartbeat_at"]),
        }

    def _serialize_public_question(self, question: dict[str, Any]) -> dict[str, Any]:
        kind = question["kind"]
        short = {
            "base_info": "基础",
            "objective": "客观",
            "subjective": "主观",
            "coding": "代码",
        }.get(kind, kind)
        type_label = question.get("type") or short
        payload = {
            "id": question["id"],
            "kind": kind,
            "shortLabel": short,
            "typeLabel": type_label,
            "title": question["title"],
            "description": question.get("description") or "",
            "score": question["score"],
        }
        if kind == "base_info":
            payload["fields"] = deepcopy(question.get("fields") or [])
        if kind == "objective":
            payload["options"] = deepcopy(question.get("options") or [])
        if kind == "coding":
            payload["language"] = question.get("language")
            payload["supportedLanguages"] = deepcopy(question.get("supported_languages") or [])
            payload["starterCode"] = question.get("starter_code")
        return payload
