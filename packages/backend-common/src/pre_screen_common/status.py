"""Canonical status codes and legacy Chinese label aliases."""

from __future__ import annotations

# --- Candidate screening ---

CANDIDATE_RESUME_UPLOADED = "resume_uploaded"
CANDIDATE_EXTRACTING = "extracting"
CANDIDATE_PROFILING = "profiling"
CANDIDATE_PENDING_REVIEW = "pending_review"
CANDIDATE_PAPER_GENERATING = "paper_generating"
CANDIDATE_READY_TO_PUBLISH = "ready_to_publish"
CANDIDATE_PAPER_SENT = "paper_sent"
CANDIDATE_EXAM_IN_PROGRESS = "exam_in_progress"
CANDIDATE_SUBMITTED = "submitted"
CANDIDATE_REVIEWING = "reviewing"
CANDIDATE_SCREENING_PASSED = "screening_passed"
CANDIDATE_SCREENING_REJECTED = "screening_rejected"
CANDIDATE_ARCHIVED = "archived"

CANDIDATE_LABELS: dict[str, str] = {
    CANDIDATE_RESUME_UPLOADED: "已上传简历",
    CANDIDATE_EXTRACTING: "信息提取中",
    CANDIDATE_PROFILING: "信息整理中",
    CANDIDATE_PENDING_REVIEW: "待审核",
    CANDIDATE_PAPER_GENERATING: "拟出卷中",
    CANDIDATE_READY_TO_PUBLISH: "待发卷",
    CANDIDATE_PAPER_SENT: "已发卷",
    CANDIDATE_EXAM_IN_PROGRESS: "进行中考试",
    CANDIDATE_SUBMITTED: "已交卷",
    CANDIDATE_REVIEWING: "评分复核中",
    CANDIDATE_SCREENING_PASSED: "已完成筛选",
    CANDIDATE_SCREENING_REJECTED: "已淘汰",
    CANDIDATE_ARCHIVED: "已归档",
}

_LEGACY_CANDIDATE_LABEL_TO_CODE: dict[str, str] = {
    "已上传简历": CANDIDATE_RESUME_UPLOADED,
    "解析中": CANDIDATE_EXTRACTING,
    "信息提取中": CANDIDATE_EXTRACTING,
    "信息整理中": CANDIDATE_PROFILING,
    "待审核": CANDIDATE_PENDING_REVIEW,
    "拟出卷中": CANDIDATE_PAPER_GENERATING,
    "待发卷": CANDIDATE_READY_TO_PUBLISH,
    "已发卷": CANDIDATE_PAPER_SENT,
    "待开考": CANDIDATE_PAPER_SENT,
    "已开考": CANDIDATE_EXAM_IN_PROGRESS,
    "进行中考试": CANDIDATE_EXAM_IN_PROGRESS,
    "已交卷": CANDIDATE_SUBMITTED,
    "已完成": CANDIDATE_SUBMITTED,
    "评分复核中": CANDIDATE_REVIEWING,
    "已完成筛选": CANDIDATE_SCREENING_PASSED,
    "已淘汰": CANDIDATE_SCREENING_REJECTED,
    "已归档": CANDIDATE_ARCHIVED,
}

SCREENING_IN_PROGRESS_CODES = frozenset(
    {
        CANDIDATE_EXTRACTING,
        CANDIDATE_PROFILING,
        CANDIDATE_PENDING_REVIEW,
        CANDIDATE_RESUME_UPLOADED,
    }
)
EXAM_IN_PROGRESS_CODES = frozenset({CANDIDATE_EXAM_IN_PROGRESS})
SCREENING_COMPLETED_CODES = frozenset(
    {CANDIDATE_SCREENING_PASSED, CANDIDATE_ARCHIVED, CANDIDATE_SCREENING_REJECTED}
)

# --- Paper / session / result ---

PAPER_DRAFT = "draft"
PAPER_PUBLISHED = "published"

SESSION_IN_PROGRESS = "in_progress"
SESSION_SUBMITTED = "submitted"
SESSION_EXPIRED = "expired"

RESULT_SUBMITTED = "submitted"
RESULT_REVIEWED = "reviewed"
RESULT_COMPLETED = "completed"

REVIEW_PENDING = "pending"
REVIEW_REVIEWING = "reviewing"
REVIEW_REVIEWED = "reviewed"

DECISION_PASS = "pass"
DECISION_REJECT = "reject"

TASK_OPEN = "open"
TASK_CLOSED = "closed"

UPLOAD_QUEUED = "queued"
UPLOAD_RUNNING = "running"
UPLOAD_PARSED = "parsed"
UPLOAD_FAILED = "failed"


def normalize_candidate_status(value: str | None) -> str:
    if not value:
        return CANDIDATE_RESUME_UPLOADED
    if value in CANDIDATE_LABELS:
        return value
    return _LEGACY_CANDIDATE_LABEL_TO_CODE.get(value, value)


def candidate_status_label(code_or_label: str | None) -> str:
    code = normalize_candidate_status(code_or_label)
    return CANDIDATE_LABELS.get(code, code_or_label or "")


def is_screening_in_progress(status: str | None) -> bool:
    return normalize_candidate_status(status) in SCREENING_IN_PROGRESS_CODES


def is_exam_in_progress(status: str | None) -> bool:
    return normalize_candidate_status(status) in EXAM_IN_PROGRESS_CODES


def is_screening_completed(status: str | None) -> bool:
    return normalize_candidate_status(status) in SCREENING_COMPLETED_CODES


def is_ready_to_publish(status: str | None) -> bool:
    return normalize_candidate_status(status) == CANDIDATE_READY_TO_PUBLISH
