from copy import deepcopy

from fastapi import APIRouter, HTTPException

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
    return {"items": deepcopy(_CANDIDATES), "total": len(_CANDIDATES)}


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str) -> dict:
    candidate = _CANDIDATE_DETAILS.get(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return deepcopy(candidate)


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: str) -> dict:
    paper = _PAPER_DRAFTS.get(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper draft not found.")
    return deepcopy(paper)
