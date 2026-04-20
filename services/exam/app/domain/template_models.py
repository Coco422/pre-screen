from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True, frozen=True)
class TemplateConfig:
    objective_count: int
    subjective_count: int
    coding_count: int
    base_info_count: int = 1


@dataclass(slots=True, frozen=True)
class JobTemplate:
    template_id: str
    name: str
    role_type: str
    level: str
    template_config: TemplateConfig
    tags: tuple[str, ...] = field(default_factory=tuple)
    copied_from_template_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data
