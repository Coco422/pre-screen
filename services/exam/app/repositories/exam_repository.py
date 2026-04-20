from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import randbelow, token_urlsafe
from uuid import uuid4

from services.exam.app.domain.template_models import JobTemplate, TemplateConfig


class ExamRepository:
    def __init__(self) -> None:
        self._templates: dict[str, JobTemplate] = {}
        self._paper_drafts: list[dict] = []
        self._invitations: dict[str, dict] = {}
        self._sessions: dict[str, dict] = {}
        self._answers: dict[tuple[str, str], dict] = {}

    def reset(self) -> None:
        self._templates.clear()
        self._paper_drafts.clear()
        self._invitations.clear()
        self._sessions.clear()
        self._answers.clear()

    def create_template(
        self,
        *,
        name: str,
        role_type: str,
        level: str,
        template_config: dict,
        tags: list[str] | None = None,
        copied_from_template_id: str | None = None,
    ) -> JobTemplate:
        template = JobTemplate(
            template_id=uuid4().hex,
            name=name,
            role_type=role_type,
            level=level,
            template_config=TemplateConfig(**template_config),
            tags=tuple(tags or []),
            copied_from_template_id=copied_from_template_id,
        )
        self._templates[template.template_id] = template
        return template

    def list_templates(self) -> list[JobTemplate]:
        return list(self._templates.values())

    def get_template(self, template_id: str) -> JobTemplate | None:
        return self._templates.get(template_id)

    def clone_template(self, template_id: str, *, name: str) -> JobTemplate:
        source = self._templates[template_id]
        return self.create_template(
            name=name,
            role_type=source.role_type,
            level=source.level,
            template_config={
                "objective_count": source.template_config.objective_count,
                "subjective_count": source.template_config.subjective_count,
                "coding_count": source.template_config.coding_count,
                "base_info_count": source.template_config.base_info_count,
            },
            tags=list(source.tags),
            copied_from_template_id=source.template_id,
        )

    def save_paper_draft(self, draft: dict) -> dict:
        self._paper_drafts.append(draft)
        return draft

    def create_invitation(self, *, exam_paper_id: str, duration_minutes: int) -> dict:
        invitation_id = uuid4().hex
        one_time_code = f"{randbelow(1_000_000):06d}"
        invitation = {
            "invitation_id": invitation_id,
            "exam_paper_id": exam_paper_id,
            "access_token": token_urlsafe(24),
            "one_time_code_hash": sha256(one_time_code.encode("utf-8")).hexdigest(),
            "duration_minutes": duration_minutes,
            "expires_at": datetime.now(UTC) + timedelta(days=3),
            "sent_status": "generated",
        }
        self._invitations[invitation_id] = invitation
        return {**invitation, "one_time_code": one_time_code}

    def get_invitation(self, invitation_id: str) -> dict | None:
        return self._invitations.get(invitation_id)

    def verify_invitation_code(self, invitation_id: str, one_time_code: str) -> bool:
        invitation = self._invitations.get(invitation_id)
        if invitation is None:
            return False
        return invitation["one_time_code_hash"] == sha256(one_time_code.encode("utf-8")).hexdigest()

    def create_session(self, *, invitation_id: str, start_at: datetime, expire_at: datetime) -> dict:
        invitation = self._invitations[invitation_id]
        session = {
            "session_id": uuid4().hex,
            "invitation_id": invitation_id,
            "exam_paper_id": invitation["exam_paper_id"],
            "status": "in_progress",
            "start_at": start_at,
            "expire_at": expire_at,
            "submitted_at": None,
            "last_heartbeat_at": start_at,
        }
        self._sessions[session["session_id"]] = session
        return session

    def get_session(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def touch_heartbeat(self, session_id: str) -> dict:
        session = self._sessions[session_id]
        session["last_heartbeat_at"] = datetime.now(UTC)
        return session

    def save_answer_draft(self, *, session_id: str, question_id: str, draft_answer: dict) -> dict:
        answer = {
            "session_id": session_id,
            "question_id": question_id,
            "draft_answer": draft_answer,
            "last_saved_at": datetime.now(UTC),
            "status": "saved",
        }
        self._answers[(session_id, question_id)] = answer
        return answer


exam_repository = ExamRepository()
