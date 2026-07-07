from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError


class ResumeModelResponse(BaseModel):
    markdown: str
    profile: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    page_summaries: list[dict] = Field(default_factory=list)


def parse_resume_model_response(content: str) -> ResumeModelResponse:
    try:
        payload = json.loads(_extract_json_text(content))
        return ResumeModelResponse.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Model response must be valid JSON with at least a markdown field.") from exc


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)
    json_object = re.search(r"(\{.*\})", stripped, flags=re.DOTALL)
    if json_object:
        return json_object.group(1)
    return stripped
