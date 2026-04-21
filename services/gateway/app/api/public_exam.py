import os
from datetime import UTC, datetime

from copy import deepcopy

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from pre_screen_common.judge0_client import Judge0Client
from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS
from services.judge_bridge.app.domain.scoring import build_submission_summary, score_case_result
from services.judge_bridge.app.tasks.poll_submission import execute_sync_case

router = APIRouter(prefix="/public", tags=["gateway-public"])


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

_EXAM_SHELL = {
    "paper_title": "技术岗在线考核",
    "duration_minutes": 90,
    "heartbeat_interval_ms": 15000,
    "autosave_interval_ms": 1200,
    "risk_events": [
        "window_blur",
        "page_hidden",
        "copy",
        "paste",
        "network_offline",
        "network_online",
    ],
    "questions": [
        {
            "id": "q-base-1",
            "kind": "base_info",
            "short_label": "基础信息",
            "type_label": "基础信息",
            "title": "补充基础信息",
            "description": "请补全个人基础信息，方便 HR 结合岗位需求做后续沟通。",
            "score": 0,
            "fields": ["身高", "体重", "爱好", "可到岗时间"],
        },
        {
            "id": "q-obj-1",
            "kind": "objective",
            "short_label": "客观题 1",
            "type_label": "客观题",
            "title": "Vue 响应式原理基础",
            "description": "请选出最符合 Vue 响应式更新机制的描述。",
            "score": 5,
            "options": [
                "Proxy 劫持并按依赖触发更新",
                "通过轮询监听数据变化",
                "只依赖模板字符串解析",
            ],
        },
        {
            "id": "q-sub-1",
            "kind": "subjective",
            "short_label": "主观题",
            "type_label": "主观题",
            "title": "请复盘一个你最熟悉的项目",
            "description": "重点讲清楚你的角色、最难的一段、以及如何验证结果。",
            "score": 15,
        },
        {
            "id": "q-code-1",
            "kind": "coding",
            "short_label": "代码题",
            "type_label": "代码题",
            "title": "实现一个数组去重函数",
            "description": "请从标准输入读取一个 JSON 数组，输出保持顺序稳定的去重结果，例如输入 [1,1,2,3,2] 输出 [1,2,3]。",
            "score": 50,
            "language": "JavaScript",
            "supported_languages": [
                "C",
                "C++",
                "Java",
                "Python",
                "JavaScript",
                "TypeScript",
                "Go",
                "Rust",
            ],
            "starter_code": "function unique(items) {\n  return [...new Set(items)];\n}",
        },
    ],
}

_HEARTBEATS: dict[str, dict] = {}
_ANSWER_DRAFTS: dict[tuple[str, str], dict] = {}
_RISK_EVENTS: list[dict] = []
_CODING_TESTCASES = {
    "q-code-1": [
        {"stdin": "[1,1,2,3,2]\n", "expected_stdout": "[1,2,3]\n", "score": 50},
        {"stdin": "[\"a\",\"a\",\"b\",\"c\",\"b\"]\n", "expected_stdout": "[\"a\",\"b\",\"c\"]\n", "score": 50},
    ]
}


@router.get("/exams/{token}")
async def get_exam_shell(token: str) -> dict:
    payload = deepcopy(_EXAM_SHELL)
    payload["token"] = token
    return payload


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


@router.post("/exams/{token}/heartbeat", status_code=status.HTTP_202_ACCEPTED)
async def heartbeat(token: str) -> dict:
    snapshot = {
        "token": token,
        "last_heartbeat_at": datetime.now(UTC).isoformat(),
        "status": "accepted",
    }
    _HEARTBEATS[token] = snapshot
    return snapshot


@router.put("/exams/{token}/answers/{question_id}", status_code=status.HTTP_202_ACCEPTED)
async def save_answer(token: str, question_id: str, request: SaveAnswerRequest) -> dict:
    snapshot = {
        "token": token,
        "question_id": question_id,
        "draft_answer": request.draft_answer,
        "last_saved_at": datetime.now(UTC).isoformat(),
        "status": "saved",
    }
    _ANSWER_DRAFTS[(token, question_id)] = snapshot
    return snapshot


@router.post("/exams/{token}/risk-events", status_code=status.HTTP_202_ACCEPTED)
async def create_risk_event(token: str, request: RiskEventRequest) -> dict:
    event = {
        "token": token,
        "event_type": request.event_type,
        "payload": request.payload,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _RISK_EVENTS.append(event)
    return event


@router.post("/exams/{token}/coding/run")
async def run_coding_case(token: str, request: RunCodingRequest) -> dict:
    del token
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
    del token
    testcases = _CODING_TESTCASES.get(request.question_id)
    if testcases is None:
        raise HTTPException(status_code=404, detail="Coding question not found.")

    language = _normalize_language(request.language)
    client = _get_judge_client()
    case_results = []
    for testcase in testcases:
        result = execute_sync_case(
            client,
            language=language,
            language_id=PRODUCT_LANGUAGE_IDS[language],
            source_code=request.source_code,
            stdin=testcase["stdin"],
        )
        case_results.append(score_case_result(result, testcase))

    return {
        "mode": "submit",
        "question_id": request.question_id,
        "results": case_results,
        "summary": build_submission_summary(case_results),
    }
