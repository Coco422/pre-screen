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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
