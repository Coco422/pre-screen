from copy import deepcopy
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.resume.app.domain.models import ResumeParseResult
from services.resume.app.parsing.privacy import mask_email, mask_phone
from services.resume.app.repositories.resume_repository import resume_repository

router = APIRouter(prefix="/admin", tags=["gateway-admin"])

_CANDIDATES = [
    {
        "id": "c-001",
        "name": "郭子贤",
        "role": "全栈开发工程师",
        "city": "深圳",
        "status": "待发卷",
        "quality": "高",
        "summary": "简历文本层完整，系统已提取邮箱、技能与项目亮点，建议直接生成考卷草稿。",
        "skills": ["Python", "C++", "Vue"],
    },
    {
        "id": "c-002",
        "name": "梁承与",
        "role": "前端实习生",
        "city": "广州",
        "status": "待审核",
        "quality": "中",
        "summary": "第二页低文本覆盖，已触发多模态补读，建议 HR 先检查项目细节后发卷。",
        "skills": ["Vue", "TypeScript", "工程化"],
    },
    {
        "id": "c-003",
        "name": "沈昊天",
        "role": "前端开发工程师",
        "city": "深圳",
        "status": "已开考",
        "quality": "高",
        "summary": "候选人已进入考试会话，自动保存与心跳正常，暂无异常事件。",
        "skills": ["JavaScript", "Vue", "浏览器"],
    },
]

_CANDIDATE_DETAILS = {
    "c-001": {
        "id": "c-001",
        "name": "郭子贤",
        "role": "全栈开发工程师",
        "email": "15099970619@163.com",
        "city": "深圳",
        "skills": ["Python", "Java", "C++", "Vue"],
        "project_summary": "做过权限管理、接口编排和前后端联调，整体表达清晰，技术栈跨度较大。",
        "parse_metrics": {
            "first_page_characters": 1740,
            "multimodal_pages": 1,
            "confidence": "高",
        },
        "review_notes": [
            "第 2 页低文本覆盖，已触发多模态补读。",
            "基础信息字段完整，暂无人工修正。",
        ],
        "next_actions": [
            {"label": "生成考卷草稿", "target": "/admin/papers/p-001"},
            {"label": "修正候选人画像", "target": "/admin/candidates/c-001/edit"},
        ],
    }
}

_PAPER_DRAFTS = {
    "p-001": {
        "paper_id": "p-001",
        "title": "前端实习生考卷草稿",
        "mix": {
            "base_info": 1,
            "objective": 4,
            "subjective": 2,
            "coding": 1,
        },
        "questions": [
            {
                "type": "基础信息",
                "title": "补充基础信息",
                "score": 0,
                "description": "填写身高、体重、爱好和可到岗时间。",
            },
            {
                "type": "客观题",
                "title": "Vue 响应式原理基础",
                "score": 5,
                "description": "根据候选人简历中的 Vue 信号优先保留。",
            },
            {
                "type": "客观题",
                "title": "TypeScript 类型系统",
                "score": 5,
                "description": "覆盖联合类型、泛型和类型收窄。",
            },
            {
                "type": "主观题",
                "title": "请复盘一个你最熟悉的项目",
                "score": 15,
                "description": "聚焦完整度、角色边界和复盘深度。",
            },
            {
                "type": "代码题",
                "title": "实现一个数组去重函数",
                "score": 50,
                "description": "支持多语言，后续将接 Judge Bridge 判题。",
            },
        ],
    }
}


@router.get("/candidates")
async def list_candidates() -> dict:
    parsed = resume_repository.list_parse_results()
    if parsed:
        items = [_candidate_card_from_parse_result(result) for result in parsed]
        return {"items": items, "total": len(items)}
    return {"items": deepcopy(_CANDIDATES), "total": len(_CANDIDATES)}


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str, include_pii: bool = False) -> dict:
    parsed = resume_repository.get_parse_result(candidate_id)
    if parsed is not None:
        return _candidate_detail_from_parse_result(
            parsed,
            include_pii=include_pii and os.environ.get("APP_ENV", "local") == "local",
        )
    candidate = _CANDIDATE_DETAILS.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return deepcopy(candidate)


@router.get("/candidates/{candidate_id}/avatar")
async def get_candidate_avatar(candidate_id: str) -> FileResponse:
    parsed = resume_repository.get_parse_result(candidate_id)
    if parsed is None or not parsed.avatar.image_path:
        raise HTTPException(status_code=404, detail="Candidate avatar not found.")
    return FileResponse(parsed.avatar.image_path)


@router.get("/resume-batches/latest/analysis")
async def get_latest_resume_batch_analysis() -> dict:
    latest = resume_repository.latest_batch_result()
    if latest is None:
        return {
            "batch_id": None,
            "analysis_markdown": (
                "# 简历批量共性分析\n\n"
                "暂无真实批量解析结果。上传或运行批处理后，这里会展示技能矩阵、共性主题和复核提示。\n"
            ),
        }
    return {
        "batch_id": latest.batch_id,
        "output_dir": latest.output_dir,
        "analysis_markdown": latest.analysis_markdown,
    }


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: str) -> dict:
    paper = _PAPER_DRAFTS.get(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper draft not found.")
    return deepcopy(paper)


def _candidate_card_from_parse_result(result: ResumeParseResult) -> dict:
    profile = result.profile
    warnings = result.metadata.get("warnings", [])
    return {
        "id": result.file_id,
        "name": profile.get("name") or result.candidate_name,
        "role": profile.get("role") or _role_from_filename(result.original_filename),
        "city": profile.get("city") or "未识别",
        "status": "待审核" if warnings else "待发卷",
        "quality": _parse_quality(result),
        "summary": profile.get("summary") or "已完成简历解析，等待 HR 复核后生成考卷草稿。",
        "skills": profile.get("skills", [])[:8],
    }


def _candidate_detail_from_parse_result(result: ResumeParseResult, *, include_pii: bool) -> dict:
    profile = result.profile
    phone = profile.get("phone")
    email = profile.get("email")
    if not include_pii:
        phone = mask_phone(phone)
        email = mask_email(email)

    first_page_characters = 0
    multimodal_pages = 0
    for item in profile.get("page_metrics", []):
        if item.get("page_number") == 1:
            first_page_characters = item.get("text_chars", 0)
        if item.get("needs_multimodal"):
            multimodal_pages += 1

    avatar_url = None
    if result.avatar.status == "found" and result.avatar.image_path and Path(result.avatar.image_path).exists():
        avatar_url = f"/admin/candidates/{result.file_id}/avatar"

    return {
        "id": result.file_id,
        "name": profile.get("name") or result.candidate_name,
        "role": profile.get("role") or _role_from_filename(result.original_filename),
        "phone": phone,
        "email": email,
        "city": profile.get("city") or "未识别",
        "skills": profile.get("skills", [])[:12],
        "project_summary": profile.get("summary") or "已完成简历解析，等待人工复核。",
        "markdown_preview": result.markdown,
        "avatar_url": avatar_url,
        "parse_metrics": {
            "first_page_characters": first_page_characters,
            "multimodal_pages": multimodal_pages,
            "confidence": _parse_quality(result),
        },
        "review_notes": result.metadata.get("warnings", [])[:8] or ["基础信息字段已提取，请复核项目贡献深度。"],
        "next_actions": [
            {"label": "生成考卷草稿", "target": "/admin/papers/p-001"},
            {"label": "查看原始 Markdown", "target": f"/admin/candidates/{result.file_id}"},
        ],
    }


def _parse_quality(result: ResumeParseResult) -> str:
    warnings = result.metadata.get("warnings", [])
    text_length = result.metadata.get("text_length", 0)
    if not warnings and text_length >= 1200:
        return "高"
    if text_length >= 800:
        return "中"
    return "低"


def _role_from_filename(filename: str) -> str:
    if "前端" in filename:
        return "前端开发工程师"
    if "全栈" in filename:
        return "全栈开发工程师"
    return "技术岗"
