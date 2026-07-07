from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True, frozen=True)
class ResumeUpload:
    upload_id: str
    candidate_name: str
    original_filename: str
    object_key: str
    content_type: str
    size_bytes: int
    local_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True, frozen=True)
class AvatarAsset:
    status: str
    page_number: int | None = None
    xref: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    image_path: str | None = None
    width: int | None = None
    height: int | None = None
    reason: str | None = None


@dataclass(slots=True, frozen=True)
class ResumeParseResult:
    file_id: str
    candidate_name: str
    original_filename: str
    markdown: str
    profile: dict
    metadata: dict
    avatar: AvatarAsset
    parse_status: str = "parsed"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True, frozen=True)
class ResumeBatchResult:
    batch_id: str
    file_ids: tuple[str, ...]
    output_dir: str
    analysis_markdown: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
