import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from pre_screen_common.judge0_client import Judge0Client
from services.gateway.app.domain.store_router import gateway_store
from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS
from services.judge_bridge.app.domain.scoring import build_submission_summary, score_case_result
from services.judge_bridge.app.tasks.poll_submission import execute_sync_case

router = APIRouter(prefix="/public", tags=["gateway-public"])


class StartExamRequest(BaseModel):
    verification_code: str


class SaveAnswerRequest(BaseModel):
    draft_answer: dict = Field(default_factory=dict)


class RiskEventRequest(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)


class RunCodingRequest(BaseModel):
    language: str
    source_code: str
    stdin: str = ""


class SubmitCodingRequest(BaseModel):
    question_id: str
    language: str
    source_code: str


def _get_judge_client() -> Judge0Client:
    return Judge0Client(base_url=os.environ.get("JUDGE0_BASE_URL", "http://judge0:2358"))


def _normalize_language(language: str) -> str:
    aliases = {
        "c": "c",
        "c++": "cpp",
        "cpp": "cpp",
        "java": "java",
        "python": "python",
        "javascript": "javascript",
        "js": "javascript",
        "typescript": "typescript",
        "ts": "typescript",
        "go": "go",
        "rust": "rust",
    }
    key = aliases.get(language.strip().lower())
    if key is None or key not in PRODUCT_LANGUAGE_IDS:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
    return key


@router.get("/exams/{token}")
async def get_exam_shell(token: str) -> dict:
    try:
        return gateway_store.get_exam_payload(token)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/exams/{token}/start", status_code=status.HTTP_201_CREATED)
async def start_exam(token: str, request: StartExamRequest) -> dict:
    try:
        return gateway_store.start_exam(token, request.verification_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/exams/{token}/heartbeat", status_code=status.HTTP_202_ACCEPTED)
async def heartbeat(token: str) -> dict:
    try:
        return gateway_store.heartbeat(token)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/exams/{token}/answers/{question_id}", status_code=status.HTTP_202_ACCEPTED)
async def save_answer(token: str, question_id: str, request: SaveAnswerRequest) -> dict:
    try:
        return gateway_store.save_answer(token, question_id, request.draft_answer)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/exams/{token}/risk-events", status_code=status.HTTP_202_ACCEPTED)
async def create_risk_event(token: str, request: RiskEventRequest) -> dict:
    try:
        return gateway_store.record_risk_event(token, request.event_type, request.payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/exams/{token}/coding/run")
async def run_coding_case(token: str, request: RunCodingRequest) -> dict:
    try:
        gateway_store._require_active_session(token)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    language = _normalize_language(request.language)
    result = execute_sync_case(
        _get_judge_client(),
        language=language,
        language_id=PRODUCT_LANGUAGE_IDS[language],
        source_code=request.source_code,
        stdin=request.stdin,
    )
    return {
        "mode": "run",
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr"),
        "compile_output": result.get("compile_output"),
        "status": result.get("status"),
    }


@router.post("/exams/{token}/coding/submit")
async def submit_coding_case(token: str, request: SubmitCodingRequest) -> dict:
    try:
        question = gateway_store.get_coding_question(token, request.question_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    language = _normalize_language(request.language)
    client = _get_judge_client()
    case_results = []
    for testcase in question["testcases"]:
        result = execute_sync_case(
            client,
            language=language,
            language_id=PRODUCT_LANGUAGE_IDS[language],
            source_code=request.source_code,
            stdin=testcase["stdin"],
        )
        case_results.append(score_case_result(result, testcase))

    response = {
        "mode": "submit",
        "question_id": request.question_id,
        "results": case_results,
        "summary": build_submission_summary(case_results),
    }
    gateway_store.store_coding_submission(
        token,
        request.question_id,
        language=request.language,
        source_code=request.source_code,
        result=response,
    )
    return response


@router.post("/exams/{token}/submit")
async def submit_exam(token: str) -> dict:
    try:
        return gateway_store.submit_exam(token)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
