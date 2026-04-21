import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from pre_screen_common.judge0_client import Judge0Client
from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS
from services.judge_bridge.app.domain.scoring import build_submission_summary, score_case_result
from services.judge_bridge.app.tasks.poll_submission import execute_sync_case


class RunCodeRequest(BaseModel):
    language: str
    source_code: str
    stdin: str = ""


class TestcasePayload(BaseModel):
    stdin: str = ""
    expected_stdout: str = ""
    score: int = 0


class SubmitCodeRequest(BaseModel):
    language: str
    source_code: str
    testcases: list[TestcasePayload] = Field(default_factory=list)


router = APIRouter(prefix="/internal/judge", tags=["judge"])


def _get_client() -> Judge0Client:
    return Judge0Client(base_url=os.environ.get("JUDGE0_BASE_URL", "http://judge0:2358"))


def _resolve_language(language: str) -> int:
    try:
        return PRODUCT_LANGUAGE_IDS[language]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}") from exc


@router.post("/run")
async def run_code(request: RunCodeRequest) -> dict:
    language_id = _resolve_language(request.language)
    client = _get_client()
    result = execute_sync_case(
        client,
        language=request.language,
        language_id=language_id,
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


@router.post("/submit")
async def submit_code(request: SubmitCodeRequest) -> dict:
    language_id = _resolve_language(request.language)
    client = _get_client()

    case_results = []
    for testcase in request.testcases:
        result = execute_sync_case(
            client,
            language=request.language,
            language_id=language_id,
            source_code=request.source_code,
            stdin=testcase.stdin,
        )
        case_results.append(score_case_result(result, testcase.model_dump()))

    return {
        "mode": "submit",
        "results": case_results,
        "summary": build_submission_summary(case_results),
    }
