from typing import Annotated

from fastapi import APIRouter, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from services.gateway.app.domain.demo_store import gateway_demo_store

router = APIRouter(prefix="/admin", tags=["gateway-admin"])


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateTaskRequest(BaseModel):
    title: str
    department: str
    city: str
    jd_text: str
    tags: list[str] = Field(default_factory=list)
    template_config: dict
    duration_minutes: int = Field(default=90, ge=1, le=240)


class UpdateCandidateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    email: str | None = None
    city: str | None = None
    phone: str | None = None
    skills: list[str] | None = None
    hobbies: list[str] | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    available_in_days: int | None = None
    project_summary: str | None = None
    review_note: str | None = None
    review_notes: list[str] | None = None
    projects: list[dict] | None = None


class UpdatePaperRequest(BaseModel):
    title: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=240)
    questions: list[dict] | None = None


class PublishPaperRequest(BaseModel):
    duration_minutes: int | None = Field(default=None, ge=1, le=240)


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    return authorization.split(" ", 1)[1]


def _translate_store_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Gateway demo store error.")


@router.post("/session/login")
async def login(request: LoginRequest) -> dict:
    try:
        return gateway_demo_store.login(request.username, request.password)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.get("/session/me")
async def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    try:
        return gateway_demo_store.get_current_user(_extract_bearer_token(authorization))
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.get("/tasks")
async def list_tasks(status: str | None = None, keyword: str | None = None) -> dict:
    return gateway_demo_store.list_tasks(status=status, keyword=keyword)


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(request: CreateTaskRequest) -> dict:
    return gateway_demo_store.create_task(request.model_dump())


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    try:
        return gateway_demo_store.get_task(task_id)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.post("/tasks/{task_id}/uploads", status_code=status.HTTP_202_ACCEPTED)
async def create_uploads(task_id: str, files: Annotated[list[UploadFile], File()]) -> dict:
    uploaded_items = []
    for file in files:
        uploaded_items.append(
            {
                "filename": file.filename or "resume.pdf",
                "content": await file.read(),
            }
        )
    try:
        return gateway_demo_store.create_uploads(task_id, uploaded_items)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.get("/uploads/{upload_id}")
async def get_upload(upload_id: str) -> dict:
    try:
        return gateway_demo_store.get_upload(upload_id)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.get("/candidates")
async def list_candidates(task_id: str | None = None, status: str | None = None) -> dict:
    return gateway_demo_store.list_candidates(task_id=task_id, status=status)


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str) -> dict:
    try:
        return gateway_demo_store.get_candidate(candidate_id)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.put("/candidates/{candidate_id}")
async def update_candidate(candidate_id: str, request: UpdateCandidateRequest) -> dict:
    try:
        return gateway_demo_store.update_candidate(candidate_id, request.model_dump())
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.post("/candidates/{candidate_id}/papers/generate", status_code=status.HTTP_201_CREATED)
async def generate_paper(candidate_id: str) -> dict:
    try:
        return gateway_demo_store.generate_paper(candidate_id)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: str) -> dict:
    try:
        return gateway_demo_store.get_paper(paper_id)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.put("/papers/{paper_id}")
async def update_paper(paper_id: str, request: UpdatePaperRequest) -> dict:
    try:
        return gateway_demo_store.update_paper(paper_id, request.model_dump())
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.post("/papers/{paper_id}/publish", status_code=status.HTTP_201_CREATED)
async def publish_paper(paper_id: str, request: PublishPaperRequest) -> dict:
    try:
        return gateway_demo_store.publish_paper(paper_id, request.duration_minutes)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc


@router.get("/results")
async def list_results(status: str | None = None, task_id: str | None = None) -> dict:
    return gateway_demo_store.list_results(status=status, task_id=task_id)


@router.get("/results/{result_id}")
async def get_result(result_id: str) -> dict:
    try:
        return gateway_demo_store.get_result(result_id)
    except Exception as exc:  # pragma: no cover
        raise _translate_store_error(exc) from exc
