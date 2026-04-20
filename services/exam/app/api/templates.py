from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.exam.app.repositories.exam_repository import exam_repository


class TemplateConfigPayload(BaseModel):
    objective_count: int
    subjective_count: int
    coding_count: int
    base_info_count: int = 1


class CreateTemplateRequest(BaseModel):
    name: str
    role_type: str
    level: str
    template_config: TemplateConfigPayload
    tags: list[str] = Field(default_factory=list)


class CloneTemplateRequest(BaseModel):
    name: str


router = APIRouter(prefix="/internal/exam/templates", tags=["exam-templates"])


@router.get("")
async def list_templates() -> dict[str, list[dict]]:
    return {"items": [item.to_dict() for item in exam_repository.list_templates()]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_template(request: CreateTemplateRequest) -> dict:
    template = exam_repository.create_template(
        name=request.name,
        role_type=request.role_type,
        level=request.level,
        template_config=request.template_config.model_dump(),
        tags=request.tags,
    )
    return template.to_dict()


@router.get("/{template_id}")
async def get_template(template_id: str) -> dict:
    template = exam_repository.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    return template.to_dict()


@router.post("/{template_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_template(template_id: str, request: CloneTemplateRequest) -> dict:
    if exam_repository.get_template(template_id) is None:
        raise HTTPException(status_code=404, detail="Template not found.")
    cloned = exam_repository.clone_template(template_id, name=request.name)
    return cloned.to_dict()
