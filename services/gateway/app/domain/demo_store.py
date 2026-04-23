from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from secrets import randbelow, token_urlsafe
from tempfile import TemporaryDirectory
from threading import RLock, Thread
from typing import Any

from services.exam.app.domain.paper_generator import generate_paper_draft
from services.gateway.app.domain.resume_intelligence import build_question_brief, enrich_resume_profile
from services.resume.app.tasks.parse_resume import parse_resume_file
from services.scoring.app.domain.objective import score_objective_answer
from services.scoring.app.domain.subjective import suggest_subjective_score
from services.scoring.app.domain.summary import build_score_summary

HEARTBEAT_INTERVAL_MS = 15_000
AUTOSAVE_INTERVAL_MS = 1_200
RISK_EVENT_TYPES = [
    "window_blur",
    "page_hidden",
    "copy",
    "paste",
    "network_offline",
    "network_online",
]
SUPPORTED_LANGUAGES = [
    "C",
    "C++",
    "Java",
    "Python",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
]
DEFAULT_STARTER_CODE = "function unique(items) {\n  return [...new Set(items)];\n}"
DEFAULT_CODING_TESTCASES = [
    {"stdin": "[1,1,2,3,2]\n", "expected_stdout": "[1,2,3]\n", "score": 50},
    {"stdin": "[\"a\",\"a\",\"b\",\"c\",\"b\"]\n", "expected_stdout": "[\"a\",\"b\",\"c\"]\n", "score": 50},
]

OBJECTIVE_DETAILS: dict[str, dict[str, Any]] = {
    "obj-vue-reactivity": {
        "description": "请选出最符合 Vue 响应式更新机制的描述。",
        "options": [
            "Proxy 劫持并按依赖触发更新",
            "通过轮询监听数据变化",
            "只依赖模板字符串解析",
        ],
        "answer_key": "Proxy 劫持并按依赖触发更新",
        "mode": "single_select",
    },
    "obj-typescript-types": {
        "description": "哪种方式最适合表达一个只读的联合类型集合？",
        "options": [
            "使用 readonly 数组与字面量联合类型",
            "所有场景都改成 any",
            "只通过注释声明类型",
        ],
        "answer_key": "使用 readonly 数组与字面量联合类型",
        "mode": "single_select",
    },
    "obj-engineering-build": {
        "description": "哪项最能帮助前端工程化构建稳定落地？",
        "options": [
            "统一 lint/test/build 流程",
            "每位同学自由选择构建方式",
            "上线前手工修改产物",
        ],
        "answer_key": "统一 lint/test/build 流程",
        "mode": "single_select",
    },
    "obj-browser-network": {
        "description": "浏览器缓存协商更新依赖哪个响应头语义最直接？",
        "options": ["ETag / If-None-Match", "Only Cookie", "Only Referer"],
        "answer_key": "ETag / If-None-Match",
        "mode": "single_select",
    },
    "obj-javascript-runtime": {
        "description": "关于事件循环，下列哪项描述更准确？",
        "options": [
            "微任务会在当前宏任务结束后优先执行",
            "setTimeout 一定先于 Promise.then",
            "JavaScript 没有任务队列",
        ],
        "answer_key": "微任务会在当前宏任务结束后优先执行",
        "mode": "single_select",
    },
    "obj-rest-idempotency": {
        "description": "当接口需要支持重试时，哪种做法最能体现幂等设计？",
        "options": [
            "为请求增加业务幂等键并在服务端去重",
            "每次重试都生成全新资源",
            "只在前端做按钮防抖即可",
        ],
        "answer_key": "为请求增加业务幂等键并在服务端去重",
        "mode": "single_select",
    },
    "obj-rag-retrieval": {
        "description": "关于 RAG 系统中的召回与生成，下列哪项更准确？",
        "options": [
            "应先做召回/重排，再把高相关上下文交给生成模型",
            "只要模型够大，就不需要检索",
            "把所有文档直接拼进 prompt 最稳定",
        ],
        "answer_key": "应先做召回/重排，再把高相关上下文交给生成模型",
        "mode": "single_select",
    },
    "obj-auth-session": {
        "description": "关于前后端鉴权与 Token 刷新，下列哪项更稳妥？",
        "options": [
            "通过统一拦截器处理失效重试，并限制刷新链路",
            "每个页面自己手写一套刷新逻辑",
            "Token 过期后只提示用户刷新页面",
        ],
        "answer_key": "通过统一拦截器处理失效重试，并限制刷新链路",
        "mode": "single_select",
    },
    "q-obj-1": {
        "description": "请选出最符合 Vue 响应式更新机制的描述。",
        "options": [
            "Proxy 劫持并按依赖触发更新",
            "通过轮询监听数据变化",
            "只依赖模板字符串解析",
        ],
        "answer_key": "Proxy 劫持并按依赖触发更新",
        "mode": "single_select",
    },
}

SUBJECTIVE_DETAILS: dict[str, dict[str, Any]] = {
    "sub-project-review": {
        "description": "重点讲清楚你的角色、最难的一段、以及如何验证结果。",
        "rubric_text": "项目 技术 问题 优化 性能 复盘 系统",
    },
    "sub-debug-story": {
        "description": "描述一次你定位线上问题并恢复服务的过程。",
        "rubric_text": "问题 定位 数据 日志 复盘 系统",
    },
    "sub-tech-tradeoff": {
        "description": "说说一次技术取舍，你如何平衡速度、质量与可维护性。",
        "rubric_text": "技术 取舍 质量 性能 复盘 系统",
    },
    "q-sub-1": {
        "description": "重点讲清楚你的角色、最难的一段、以及如何验证结果。",
        "rubric_text": "项目 技术 问题 优化 性能 复盘 系统",
    },
}

CODING_DETAILS: dict[str, dict[str, Any]] = {
    "code-array-dedupe-js": {
        "description": "请从标准输入读取一个 JSON 数组，输出保持顺序稳定的去重结果，例如输入 [1,1,2,3,2] 输出 [1,2,3]。",
        "language": "JavaScript",
        "supported_languages": SUPPORTED_LANGUAGES,
        "starter_code": DEFAULT_STARTER_CODE,
        "testcases": DEFAULT_CODING_TESTCASES,
    },
    "q-code-1": {
        "description": "请从标准输入读取一个 JSON 数组，输出保持顺序稳定的去重结果，例如输入 [1,1,2,3,2] 输出 [1,2,3]。",
        "language": "JavaScript",
        "supported_languages": SUPPORTED_LANGUAGES,
        "starter_code": DEFAULT_STARTER_CODE,
        "testcases": DEFAULT_CODING_TESTCASES,
    },
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


PROCESSING_STEP_LABELS = {
    "upload": "接收 PDF",
    "pdf_parse": "提取文本层",
    "project_extract": "整理项目经历",
    "paper_generate": "生成项目相关考卷",
    "paper_publish": "发布考试入口",
}


def _build_processing(
    *,
    stage: str,
    status: str,
    progress: int,
    message: str,
    step_statuses: dict[str, str] | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    statuses = step_statuses or {}
    return {
        "stage": stage,
        "status": status,
        "progress": progress,
        "message": message,
        "error_message": error_message,
        "steps": {
            key: {
                "label": label,
                "status": statuses.get(key, "pending"),
            }
            for key, label in PROCESSING_STEP_LABELS.items()
        },
    }


class GatewayDemoStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._generation = 0
        self._tempdir: TemporaryDirectory[str] | None = None
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._generation += 1
            if self._tempdir is not None:
                self._tempdir.cleanup()
            self._tempdir = TemporaryDirectory(prefix="gateway-demo-")
            self.admin_sessions: dict[str, dict[str, Any]] = {}
            self.tasks: dict[str, dict[str, Any]] = {}
            self.uploads: dict[str, dict[str, Any]] = {}
            self.candidates: dict[str, dict[str, Any]] = {}
            self.papers: dict[str, dict[str, Any]] = {}
            self.exam_tokens: dict[str, dict[str, Any]] = {}
            self.sessions: dict[str, dict[str, Any]] = {}
            self.results: dict[str, dict[str, Any]] = {}
            self._counters = {
                "task": 2,
                "upload": 6,
                "candidate": 6,
                "paper": 3,
                "session": 3,
                "result": 2,
            }
            self._seed_demo_data()

    def _seed_demo_data(self) -> None:
        now = _utcnow()
        task_created_at = now - timedelta(days=2)
        task_id = "t-001"
        self.tasks[task_id] = {
            "task_id": task_id,
            "title": "前端技术筛选",
            "department": "技术招聘",
            "city": "深圳",
            "jd_text": "需要 Vue、TypeScript、JavaScript 经验，有在线考试和后台项目经历加分。",
            "tags": ["Vue", "TypeScript", "frontend"],
            "template_config": {
                "base_info_count": 1,
                "objective_count": 4,
                "subjective_count": 2,
                "coding_count": 1,
            },
            "duration_minutes": 90,
            "status": "open",
            "created_at": task_created_at,
        }

        upload_1_created_at = now - timedelta(hours=6)
        upload_2_created_at = now - timedelta(hours=5)
        upload_3_created_at = now - timedelta(hours=4)
        upload_4_created_at = now - timedelta(hours=3)
        upload_5_created_at = now - timedelta(hours=2)

        self.uploads["u-001"] = {
            "upload_id": "u-001",
            "task_id": task_id,
            "candidate_id": "c-001",
            "filename": "guo-zixian.pdf",
            "status": "parsed",
            "progress": 100,
            "created_at": upload_2_created_at,
            "updated_at": upload_2_created_at + timedelta(minutes=18),
            "error": None,
            "pdf_path": "",
            "processing": _build_processing(
                stage="profile_ready",
                status="succeeded",
                progress=100,
                message="简历解析完成，可直接生成考卷草稿。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                },
            ),
        }
        self.uploads["u-002"] = {
            "upload_id": "u-002",
            "task_id": task_id,
            "candidate_id": "c-002",
            "filename": "liang-chengyu.pdf",
            "status": "parsed",
            "progress": 100,
            "created_at": upload_1_created_at,
            "updated_at": upload_1_created_at + timedelta(minutes=26),
            "error": None,
            "pdf_path": "",
            "processing": _build_processing(
                stage="profile_ready",
                status="succeeded",
                progress=100,
                message="文本与多模态信息已整理完毕，等待 HR 复核项目真实性。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                },
            ),
        }
        self.uploads["u-003"] = {
            "upload_id": "u-003",
            "task_id": task_id,
            "candidate_id": "c-003",
            "filename": "shen-haotian.pdf",
            "status": "parsed",
            "progress": 100,
            "created_at": upload_3_created_at,
            "updated_at": upload_3_created_at + timedelta(minutes=14),
            "error": None,
            "pdf_path": "",
            "processing": _build_processing(
                stage="published",
                status="succeeded",
                progress=100,
                message="候选人已进入考试，系统正在持续记录作答状态。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "succeeded",
                    "paper_publish": "succeeded",
                },
            ),
        }
        self.uploads["u-004"] = {
            "upload_id": "u-004",
            "task_id": task_id,
            "candidate_id": "c-004",
            "filename": "lin-qiufan.pdf",
            "status": "parsed",
            "progress": 100,
            "created_at": upload_4_created_at,
            "updated_at": upload_4_created_at + timedelta(minutes=20),
            "error": None,
            "pdf_path": "",
            "processing": _build_processing(
                stage="published",
                status="succeeded",
                progress=100,
                message="答卷已回收，等待 HR 进入结果中心复核。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "succeeded",
                    "paper_publish": "succeeded",
                },
            ),
        }
        self.uploads["u-005"] = {
            "upload_id": "u-005",
            "task_id": task_id,
            "candidate_id": "c-005",
            "filename": "zhou-yinan.pdf",
            "status": "parsed",
            "progress": 100,
            "created_at": upload_5_created_at,
            "updated_at": upload_5_created_at + timedelta(minutes=12),
            "error": None,
            "pdf_path": "",
            "processing": _build_processing(
                stage="profile_ready",
                status="succeeded",
                progress=100,
                message="筛选已完成，候选人资料已进入归档视图。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                },
            ),
        }

        self.candidates["c-001"] = {
            "candidate_id": "c-001",
            "task_id": task_id,
            "name": "郭子贤",
            "role": "全栈开发工程师",
            "email": "15099970619@163.com",
            "city": "深圳",
            "status": "待发卷",
            "quality": "高",
            "summary": "简历文本层完整，系统已提取邮箱、技能与项目亮点，建议直接生成考卷草稿。",
            "skills": ["Python", "C++", "Vue"],
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
            "paper_ids": ["p-001"],
            "latest_upload_id": "u-001",
            "created_at": upload_2_created_at,
        }
        self.candidates["c-002"] = {
            "candidate_id": "c-002",
            "task_id": task_id,
            "name": "梁承与",
            "role": "前端实习生",
            "email": None,
            "city": "广州",
            "status": "待审核",
            "quality": "中",
            "summary": "第二页低文本覆盖，已触发多模态补读，建议 HR 先检查项目细节后发卷。",
            "skills": ["Vue", "TypeScript", "工程化"],
            "project_summary": "项目表达较简略，等待人工复核补充。",
            "parse_metrics": {
                "first_page_characters": 980,
                "multimodal_pages": 2,
                "confidence": "中",
            },
            "review_notes": ["第二页低文本覆盖，待人工复核。", "项目中多次出现性能提升描述，待核实真实佐证。"],
            "paper_ids": [],
            "latest_upload_id": "u-002",
            "created_at": upload_1_created_at,
        }
        self.candidates["c-003"] = {
            "candidate_id": "c-003",
            "task_id": task_id,
            "name": "沈昊天",
            "role": "前端开发工程师",
            "email": None,
            "city": "深圳",
            "status": "已开考",
            "quality": "高",
            "summary": "候选人已进入考试会话，自动保存与心跳正常，暂无异常事件。",
            "skills": ["JavaScript", "Vue", "浏览器"],
            "project_summary": "熟悉浏览器与前端工程化，已进入在线考试。",
            "parse_metrics": {
                "first_page_characters": 1680,
                "multimodal_pages": 0,
                "confidence": "高",
            },
            "review_notes": ["考试会话已启动。"],
            "paper_ids": ["p-001"],
            "latest_upload_id": "u-003",
            "created_at": upload_3_created_at,
        }
        self.candidates["c-004"] = {
            "candidate_id": "c-004",
            "task_id": task_id,
            "name": "林秋帆",
            "role": "前端开发工程师",
            "email": "lin.qiufan@example.com",
            "city": "上海",
            "status": "已交卷",
            "quality": "高",
            "summary": "候选人已交卷，等待 HR 进入结果中心确认主观题与代码题得分。",
            "skills": ["Vue", "TypeScript", "Node.js"],
            "project_summary": "做过后台中台和在线答题系统，表达清晰，适合优先复核结果。",
            "parse_metrics": {
                "first_page_characters": 1580,
                "multimodal_pages": 0,
                "confidence": "高",
            },
            "review_notes": ["答卷已回收，待复核。"],
            "paper_ids": ["p-002"],
            "latest_upload_id": "u-004",
            "created_at": upload_4_created_at,
        }
        self.candidates["c-005"] = {
            "candidate_id": "c-005",
            "task_id": task_id,
            "name": "周以南",
            "role": "前端开发工程师",
            "email": "zhou.yinan@example.com",
            "city": "杭州",
            "status": "已完成筛选",
            "quality": "高",
            "summary": "筛选流程已完成，候选人资料已整理归档，可供后续面试参考。",
            "skills": ["React", "TypeScript", "工程化"],
            "project_summary": "项目材料完整，技术栈与岗位匹配度较高，已通过首轮筛选。",
            "parse_metrics": {
                "first_page_characters": 1660,
                "multimodal_pages": 0,
                "confidence": "高",
            },
            "review_notes": ["已完成筛选，进入归档。"],
            "paper_ids": [],
            "latest_upload_id": "u-005",
            "created_at": upload_5_created_at,
        }

        demo_questions = [
            {
                "id": "q-base-1",
                "kind": "base_info",
                "type": "基础信息",
                "title": "补充基础信息",
                "score": 0,
                "description": "请补全个人基础信息，方便 HR 结合岗位需求做后续沟通。",
                "fields": ["身高", "体重", "爱好", "可到岗时间"],
            },
            {
                "id": "q-obj-1",
                "kind": "objective",
                "type": "客观题",
                "title": "Vue 响应式原理基础",
                "score": 5,
                "description": OBJECTIVE_DETAILS["q-obj-1"]["description"],
                "options": deepcopy(OBJECTIVE_DETAILS["q-obj-1"]["options"]),
                "answer_key": OBJECTIVE_DETAILS["q-obj-1"]["answer_key"],
                "mode": OBJECTIVE_DETAILS["q-obj-1"]["mode"],
            },
            {
                "id": "q-sub-1",
                "kind": "subjective",
                "type": "主观题",
                "title": "请复盘一个你最熟悉的项目",
                "score": 15,
                "description": SUBJECTIVE_DETAILS["q-sub-1"]["description"],
                "rubric_text": SUBJECTIVE_DETAILS["q-sub-1"]["rubric_text"],
            },
            {
                "id": "q-code-1",
                "kind": "coding",
                "type": "代码题",
                "title": "实现一个数组去重函数",
                "score": 50,
                "description": CODING_DETAILS["q-code-1"]["description"],
                "language": CODING_DETAILS["q-code-1"]["language"],
                "supported_languages": deepcopy(CODING_DETAILS["q-code-1"]["supported_languages"]),
                "starter_code": CODING_DETAILS["q-code-1"]["starter_code"],
                "testcases": deepcopy(CODING_DETAILS["q-code-1"]["testcases"]),
            },
        ]
        self.papers["p-001"] = {
            "paper_id": "p-001",
            "candidate_id": "c-001",
            "task_id": task_id,
            "title": "前端实习生考卷草稿",
            "mix": {"base_info": 1, "objective": 4, "subjective": 2, "coding": 1},
            "questions": demo_questions,
            "status": "draft",
            "duration_minutes": 90,
            "created_at": now,
            "updated_at": now,
        }
        self.papers["p-002"] = {
            "paper_id": "p-002",
            "candidate_id": "c-004",
            "task_id": task_id,
            "title": "前端开发工程师在线测评",
            "mix": {"base_info": 1, "objective": 4, "subjective": 2, "coding": 1},
            "questions": deepcopy(demo_questions),
            "status": "published",
            "duration_minutes": 90,
            "created_at": upload_4_created_at + timedelta(minutes=40),
            "updated_at": upload_4_created_at + timedelta(hours=1),
        }
        session_id = "s-001"
        self.exam_tokens["token-demo"] = {
            "token": "token-demo",
            "paper_id": "p-001",
            "candidate_id": "c-003",
            "task_id": task_id,
            "verification_code_hash": sha256("123456".encode("utf-8")).hexdigest(),
            "duration_minutes": 90,
            "access_state": "in_progress",
            "created_at": now,
            "session_id": session_id,
        }
        self.exam_tokens["token-submitted"] = {
            "token": "token-submitted",
            "paper_id": "p-002",
            "candidate_id": "c-004",
            "task_id": task_id,
            "verification_code": "654321",
            "verification_code_hash": sha256("654321".encode("utf-8")).hexdigest(),
            "duration_minutes": 90,
            "access_state": "submitted",
            "created_at": upload_4_created_at + timedelta(hours=1),
            "session_id": "s-002",
        }
        self.sessions[session_id] = {
            "session_id": session_id,
            "token": "token-demo",
            "paper_id": "p-001",
            "candidate_id": "c-003",
            "task_id": task_id,
            "status": "in_progress",
            "started_at": now,
            "expires_at": now + timedelta(minutes=90),
            "submitted_at": None,
            "last_heartbeat_at": now,
            "answers": {},
            "risk_events": [],
            "result_id": None,
        }
        self.sessions["s-002"] = {
            "session_id": "s-002",
            "token": "token-submitted",
            "paper_id": "p-002",
            "candidate_id": "c-004",
            "task_id": task_id,
            "status": "completed",
            "started_at": upload_4_created_at + timedelta(hours=1),
            "expires_at": upload_4_created_at + timedelta(hours=2, minutes=30),
            "submitted_at": upload_4_created_at + timedelta(hours=2, minutes=5),
            "last_heartbeat_at": upload_4_created_at + timedelta(hours=2),
            "answers": {},
            "risk_events": [
                {"event_type": "copy", "payload": {"question_id": "q-code-1"}, "created_at": upload_4_created_at + timedelta(hours=1, minutes=30)}
            ],
            "result_id": "r-001",
        }
        self.results["r-001"] = {
            "result_id": "r-001",
            "session_id": "s-002",
            "token": "token-submitted",
            "paper_id": "p-002",
            "candidate_id": "c-004",
            "task_id": task_id,
            "status": "completed",
            "submitted_at": upload_4_created_at + timedelta(hours=2, minutes=5),
            "summary": {
                "objective_score": 24,
                "subjective_score": 26,
                "coding_score": 32,
                "total_score": 82,
                "risk_summary": {"event_count": 1, "event_types": {"copy": 1}},
            },
            "question_reviews": [
                {
                    "question_id": "q-obj-1",
                    "kind": "objective",
                    "title": "Vue 响应式原理基础",
                    "max_score": 5,
                    "draft_answer": {"answer": "Proxy 劫持并按依赖触发更新"},
                    "score": 5,
                    "result": "passed",
                }
            ],
            "risk_events": deepcopy(self.sessions["s-002"]["risk_events"]),
        }

    def _next_id(self, kind: str) -> str:
        value = self._counters[kind]
        self._counters[kind] += 1
        return f"{kind[0]}-{value:03d}"

    def login(self, username: str, password: str) -> dict[str, Any]:
        if username != "hr-demo" or password != "demo-pass":
            raise PermissionError("Invalid username or password.")
        user = {
            "user_id": "u-001",
            "username": username,
            "display_name": "Demo HR",
            "role": "hr",
        }
        token = token_urlsafe(24)
        with self._lock:
            self.admin_sessions[token] = user
        return {"token": token, "user": deepcopy(user)}

    def get_current_user(self, token: str) -> dict[str, Any]:
        user = self.admin_sessions.get(token)
        if user is None:
            raise PermissionError("Admin session is invalid.")
        return deepcopy(user)

    def get_dashboard(self) -> dict[str, Any]:
        screening_statuses = {"待审核", "解析中", "信息提取中", "信息整理中"}
        exam_in_progress_statuses = {"已开考", "进行中考试"}
        screening_completed_statuses = {"已完成筛选", "已归档"}

        screening_candidates = []
        pending_publish_candidates = []

        for candidate in self.candidates.values():
            resume_uploaded_at = self._get_candidate_resume_uploaded_at(candidate)
            profile_completed_at = self._get_candidate_profile_completed_at(candidate)

            if candidate["status"] in screening_statuses:
                screening_candidates.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "name": candidate["name"],
                        "role": candidate["role"],
                        "status": candidate["status"],
                        "resume_uploaded_at": _isoformat(resume_uploaded_at),
                        "target": f"/admin/candidates/{candidate['candidate_id']}",
                    }
                )

            if candidate["status"] == "待发卷":
                pending_publish_candidates.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "name": candidate["name"],
                        "role": candidate["role"],
                        "status": candidate["status"],
                        "profile_completed_at": _isoformat(profile_completed_at),
                        "target": f"/admin/papers/{candidate['paper_ids'][-1]}?candidateId={candidate['candidate_id']}"
                        if candidate.get("paper_ids")
                        else f"/admin/candidates/{candidate['candidate_id']}",
                    }
                )

        screening_candidates.sort(key=lambda item: item["resume_uploaded_at"] or "")
        pending_publish_candidates.sort(key=lambda item: item["profile_completed_at"] or "")

        submitted_results = [
            {
                "result_id": item["result_id"],
                "candidate_id": item["candidate_id"],
                "candidate_name": item["candidate_name"],
                "role": item["role"],
                "status": "已交卷",
                "submitted_at": item["submitted_at"],
                "total_score": item["total_score"],
                "target": f"/admin/results/{item['result_id']}",
            }
            for item in self.list_results()["items"]
        ]

        return {
            "metrics": {
                "screening_candidate_count": len(screening_candidates),
                "pending_publish_count": len(pending_publish_candidates),
                "exam_in_progress_count": sum(
                    1 for candidate in self.candidates.values() if candidate["status"] in exam_in_progress_statuses
                ),
                "submitted_count": len(submitted_results),
                "screening_completed_count": sum(
                    1
                    for candidate in self.candidates.values()
                    if candidate["status"] in screening_completed_statuses
                ),
            },
            "screening_candidates": screening_candidates[:10],
            "pending_publish_candidates": pending_publish_candidates[:10],
            "submitted_results": submitted_results[:10],
        }

    def list_tasks(self, *, status: str | None = None, keyword: str | None = None) -> dict[str, Any]:
        items = []
        for task in self.tasks.values():
            if status and task["status"] != status:
                continue
            if keyword and keyword not in task["title"] and keyword not in task["jd_text"]:
                continue
            items.append(self._serialize_task(task))
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return {"items": items, "total": len(items)}

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = self._next_id("task")
        task = {
            "task_id": task_id,
            "title": payload["title"],
            "department": payload["department"],
            "city": payload["city"],
            "jd_text": payload["jd_text"],
            "tags": list(payload.get("tags", [])),
            "template_config": deepcopy(payload["template_config"]),
            "duration_minutes": payload.get("duration_minutes", 90),
            "status": "open",
            "created_at": _utcnow(),
        }
        with self._lock:
            self.tasks[task_id] = task
        return self._serialize_task(task)

    def get_task(self, task_id: str) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        if task is None:
            raise LookupError("Task not found.")
        payload = self._serialize_task(task)
        payload["uploads"] = [
            self._serialize_upload(upload)
            for upload in self.uploads.values()
            if upload["task_id"] == task_id
        ]
        payload["candidates"] = [
            self._serialize_candidate_card(candidate)
            for candidate in self.candidates.values()
            if candidate["task_id"] == task_id
        ]
        return payload

    def create_uploads(self, task_id: str, files: list[dict[str, Any]]) -> dict[str, Any]:
        if task_id not in self.tasks:
            raise LookupError("Task not found.")
        generation = self._generation
        created_items = []
        for file_item in files:
            filename = file_item["filename"]
            content = file_item["content"]
            if not filename.lower().endswith(".pdf"):
                raise ValueError("Only PDF uploads are supported.")
            upload_id = self._next_id("upload")
            candidate_id = self._next_id("candidate")
            now = _utcnow()
            pdf_path = Path(self._tempdir.name) / f"{upload_id}.pdf"
            pdf_path.write_bytes(content)
            candidate = {
                "candidate_id": candidate_id,
                "task_id": task_id,
                "name": Path(filename).stem,
                "role": self.tasks[task_id]["title"],
                "email": None,
                "city": self.tasks[task_id]["city"],
                "status": "解析中",
                "quality": "待解析",
                "summary": "简历已上传，系统正在整理文本、项目经历与出题方向。",
                "skills": [],
                "projects": [],
                "analysis": {
                    "focus_topics": [],
                    "strengths": [],
                    "risks": [],
                    "recommended_languages": [],
                    "missing_fields": [],
                },
                "project_summary": "解析中，暂无候选人画像。",
                "parse_metrics": {
                    "first_page_characters": 0,
                    "multimodal_pages": 0,
                    "confidence": "待解析",
                },
                "review_notes": ["PDF 已上传，系统正在异步解析。"],
                "processing": _build_processing(
                    stage="uploaded",
                    status="queued",
                    progress=5,
                    message="简历已入队，等待提取文本层。",
                    step_statuses={"upload": "succeeded", "pdf_parse": "running"},
                ),
                "paper_ids": [],
                "latest_upload_id": upload_id,
                "created_at": now,
            }
            upload = {
                "upload_id": upload_id,
                "task_id": task_id,
                "candidate_id": candidate_id,
                "filename": filename,
                "status": "queued",
                "progress": 0,
                "created_at": now,
                "updated_at": now,
                "error": None,
                "pdf_path": str(pdf_path),
                "processing": _build_processing(
                    stage="uploaded",
                    status="queued",
                    progress=5,
                    message="PDF 已接收，等待开始解析。",
                    step_statuses={"upload": "succeeded", "pdf_parse": "running"},
                ),
            }
            with self._lock:
                self.candidates[candidate_id] = candidate
                self.uploads[upload_id] = upload
            created_items.append(self._serialize_upload(upload))
            Thread(target=self._parse_upload_async, args=(generation, upload_id), daemon=True).start()
        return {"items": created_items, "total": len(created_items)}

    def _parse_upload_async(self, generation: int, upload_id: str) -> None:
        with self._lock:
            upload = self.uploads.get(upload_id)
            if upload is None:
                return
            upload["status"] = "parsing"
            upload["progress"] = 35
            upload["processing"] = _build_processing(
                stage="parsing_pdf",
                status="running",
                progress=35,
                message="正在提取 PDF 文本层与页面结构。",
                step_statuses={"upload": "succeeded", "pdf_parse": "running"},
            )
            upload["updated_at"] = _utcnow()
            candidate_id = upload["candidate_id"]
            pdf_path = Path(upload["pdf_path"])
            candidate = self.candidates[candidate_id]
            candidate["processing"] = deepcopy(upload["processing"])
        try:
            render_dir = pdf_path.parent / f"{upload_id}-render"
            profile = parse_resume_file(pdf_path, render_dir=render_dir)
            rendered_images = sorted(render_dir.glob("*.png")) if render_dir.exists() else []
            with self._lock:
                if generation != self._generation or upload_id not in self.uploads:
                    return
                upload = self.uploads[upload_id]
                upload["status"] = "parsing"
                upload["progress"] = 72
                upload["processing"] = _build_processing(
                    stage="project_extract",
                    status="running",
                    progress=72,
                    message="文本层已提取，正在整理项目经历、出题焦点与推荐语言。",
                    step_statuses={
                        "upload": "succeeded",
                        "pdf_parse": "succeeded",
                        "project_extract": "running",
                    },
                )
                upload["updated_at"] = _utcnow()
                candidate = self.candidates[candidate_id]
                candidate["summary"] = "文本层已提取，系统正在整理项目经历与出题焦点。"
                candidate["processing"] = deepcopy(upload["processing"])
            enrichment = enrich_resume_profile(profile, image_paths=rendered_images)
        except Exception as exc:  # pragma: no cover
            with self._lock:
                if generation != self._generation or upload_id not in self.uploads:
                    return
                failed_upload = self.uploads[upload_id]
                failed_upload["status"] = "failed"
                failed_upload["progress"] = 100
                failed_upload["error"] = str(exc)
                failed_upload["processing"] = _build_processing(
                    stage="failed",
                    status="failed",
                    progress=100,
                    message="PDF 解析失败，请重新上传或人工处理。",
                    step_statuses={"upload": "succeeded", "pdf_parse": "failed"},
                    error_message=str(exc),
                )
                failed_upload["updated_at"] = _utcnow()
                candidate = self.candidates[candidate_id]
                candidate["status"] = "解析失败"
                candidate["quality"] = "低"
                candidate["summary"] = "简历解析失败，请重新上传或人工处理。"
                candidate["review_notes"].append(f"解析失败：{exc}")
                candidate["processing"] = deepcopy(failed_upload["processing"])
            return

        with self._lock:
            if generation != self._generation or upload_id not in self.uploads:
                return
            upload = self.uploads[upload_id]
            upload["status"] = "parsed"
            upload["progress"] = 100
            upload["processing"] = _build_processing(
                stage="profile_ready",
                status="succeeded",
                progress=100,
                message="PDF 已完成解析，项目经历与出题焦点已整理完毕。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                },
            )
            upload["updated_at"] = _utcnow()
            candidate = self.candidates[candidate_id]
            page_metrics = profile.get("page_metrics", [])
            first_page_chars = page_metrics[0]["text_chars"] if page_metrics else 0
            multimodal_pages = sum(1 for item in page_metrics if item.get("needs_multimodal"))
            risks = enrichment.get("risks", [])
            quality = "高" if multimodal_pages <= 1 and not risks else "中"
            skills = list(enrichment.get("skills", []) or profile.get("skills", []))
            candidate["name"] = enrichment.get("display_name") or profile.get("name") or candidate["name"]
            candidate["email"] = enrichment.get("email") or profile.get("email")
            candidate["phone"] = enrichment.get("phone")
            candidate["city"] = enrichment.get("city") or candidate["city"]
            candidate["skills"] = skills
            candidate["projects"] = deepcopy(enrichment.get("projects", []))
            candidate["analysis"] = {
                "focus_topics": deepcopy(enrichment.get("focus_topics", [])),
                "strengths": deepcopy(enrichment.get("strengths", [])),
                "risks": deepcopy(risks),
                "recommended_languages": deepcopy(enrichment.get("recommended_languages", [])),
                "missing_fields": deepcopy(enrichment.get("missing_fields", [])),
            }
            candidate["status"] = "待发卷"
            candidate["quality"] = quality
            candidate["summary"] = enrichment.get("profile_summary") or (
                f"简历解析完成，已提取 {', '.join(skills) or '基础信息'} 等信号，建议生成考卷草稿。"
            )
            candidate["project_summary"] = enrichment.get("project_summary") or (
                (profile.get("raw_text", "") or "暂无项目摘要。").strip()[:160]
            )
            candidate["parse_metrics"] = {
                "first_page_characters": first_page_chars,
                "multimodal_pages": multimodal_pages,
                "confidence": quality,
            }
            candidate["review_notes"] = [
                "PDF 异步解析完成。",
                *([f"已识别 {len(candidate['projects'])} 个项目卡片。"] if candidate["projects"] else []),
                *(
                    ["检测到低文本覆盖页，已触发多模态兜底。"]
                    if multimodal_pages
                    else ["文本层质量正常，未触发多模态兜底。"]
                ),
            ]
            candidate["processing"] = deepcopy(upload["processing"])

    def get_upload(self, upload_id: str) -> dict[str, Any]:
        upload = self.uploads.get(upload_id)
        if upload is None:
            raise LookupError("Upload not found.")
        return self._serialize_upload(upload)

    def list_candidates(self, *, task_id: str | None = None, status: str | None = None) -> dict[str, Any]:
        items = []
        for candidate in self.candidates.values():
            if task_id and candidate["task_id"] != task_id:
                continue
            if status and candidate["status"] != status:
                continue
            items.append(self._serialize_candidate_card(candidate))
        items.sort(key=lambda item: item["id"])
        return {"items": items, "total": len(items)}

    def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise LookupError("Candidate not found.")
        return self._serialize_candidate_detail(candidate)

    def update_candidate(self, candidate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise LookupError("Candidate not found.")
        with self._lock:
            for field in ("name", "role", "email", "city", "phone", "project_summary"):
                if payload.get(field) is not None:
                    candidate[field] = payload[field]
            if payload.get("skills") is not None:
                candidate["skills"] = list(payload["skills"])
            if payload.get("hobbies") is not None:
                candidate["hobbies"] = list(payload["hobbies"])
            for field in ("height_cm", "weight_kg", "available_in_days"):
                if field in payload:
                    candidate[field] = payload[field]
            if payload.get("projects") is not None:
                candidate["projects"] = deepcopy(payload["projects"])
            if payload.get("review_note"):
                candidate["review_notes"].append(payload["review_note"])
            if payload.get("review_notes") is not None:
                candidate["review_notes"] = list(payload["review_notes"])
            candidate["summary"] = "候选人画像已人工更新，可继续生成或调整考卷。"
        return self._serialize_candidate_detail(candidate)

    def generate_paper(self, candidate_id: str) -> dict[str, Any]:
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise LookupError("Candidate not found.")
        task = self.tasks[candidate["task_id"]]
        question_brief = build_question_brief(
            candidate_profile={
                "skills": candidate["skills"],
                "projects": deepcopy(candidate.get("projects", [])),
                "focus_topics": deepcopy(candidate.get("analysis", {}).get("focus_topics", [])),
                "recommended_languages": deepcopy(
                    candidate.get("analysis", {}).get("recommended_languages", [])
                ),
                "project_summary": candidate["project_summary"],
            },
            job_context={
                "title": task["title"],
                "department": task["department"],
                "jd_text": task["jd_text"],
                "tags": deepcopy(task["tags"]),
            },
        )
        draft = generate_paper_draft(
            job_template={
                "name": task["title"],
                **task["template_config"],
                "tags": task["tags"],
            },
            jd_text=task["jd_text"],
            candidate_profile={
                "skills": candidate["skills"],
                "projects": deepcopy(candidate.get("projects", [])),
                "focus_topics": deepcopy(candidate.get("analysis", {}).get("focus_topics", [])),
                "recommended_languages": deepcopy(
                    candidate.get("analysis", {}).get("recommended_languages", [])
                ),
                "question_brief": question_brief,
            },
        )
        paper_id = self._next_id("paper")
        paper = {
            "paper_id": paper_id,
            "candidate_id": candidate_id,
            "task_id": candidate["task_id"],
            "title": f"{task['title']}在线测评草稿",
            "mix": deepcopy(draft["question_mix"]),
            "questions": [self._materialize_question(item) for item in draft["questions"]],
            "status": "draft",
            "duration_minutes": task["duration_minutes"],
            "introduction": draft.get("introduction"),
            "generation_summary": deepcopy(draft.get("generation_summary", {})),
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        with self._lock:
            self.papers[paper_id] = paper
            candidate["paper_ids"].append(paper_id)
            candidate["status"] = "待发卷"
            candidate["processing"] = _build_processing(
                stage="paper_ready",
                status="succeeded",
                progress=100,
                message="候选人画像已完成，系统已生成项目相关考卷草稿。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "succeeded",
                },
            )
        return self._serialize_paper(paper)

    def get_paper(self, paper_id: str) -> dict[str, Any]:
        paper = self.papers.get(paper_id)
        if paper is None:
            raise LookupError("Paper draft not found.")
        return self._serialize_paper(paper)

    def update_paper(self, paper_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        paper = self.papers.get(paper_id)
        if paper is None:
            raise LookupError("Paper draft not found.")
        with self._lock:
            if payload.get("title") is not None:
                paper["title"] = payload["title"]
            if payload.get("duration_minutes") is not None:
                paper["duration_minutes"] = payload["duration_minutes"]
            if payload.get("introduction") is not None:
                paper["introduction"] = payload["introduction"]
            if payload.get("questions") is not None:
                updates = {item["id"]: item for item in payload["questions"] if item.get("id")}
                for question in paper["questions"]:
                    patch = updates.get(question["id"])
                    if patch is None:
                        continue
                    for field in (
                        "title",
                        "description",
                        "score",
                        "rubric_text",
                        "language",
                        "starter_code",
                    ):
                        if patch.get(field) is not None:
                            question[field] = patch[field]
                    if patch.get("fields") is not None:
                        question["fields"] = deepcopy(patch["fields"])
                    if patch.get("options") is not None:
                        question["options"] = deepcopy(patch["options"])
                    if patch.get("answer_key") is not None:
                        question["answer_key"] = deepcopy(patch["answer_key"])
                    if patch.get("supported_languages") is not None:
                        question["supported_languages"] = deepcopy(patch["supported_languages"])
            paper["updated_at"] = _utcnow()
        return self._serialize_paper(paper)

    def publish_paper(self, paper_id: str, duration_minutes: int | None = None) -> dict[str, Any]:
        paper = self.papers.get(paper_id)
        if paper is None:
            raise LookupError("Paper draft not found.")
        token = token_urlsafe(16)
        verification_code = f"{randbelow(1_000_000):06d}"
        published = {
            "token": token,
            "paper_id": paper_id,
            "candidate_id": paper["candidate_id"],
            "task_id": paper["task_id"],
            "verification_code": verification_code,
            "verification_code_hash": sha256(verification_code.encode("utf-8")).hexdigest(),
            "duration_minutes": duration_minutes or paper["duration_minutes"],
            "access_state": "not_started",
            "created_at": _utcnow(),
            "session_id": None,
        }
        with self._lock:
            self.exam_tokens[token] = published
            paper["status"] = "published"
            paper["updated_at"] = _utcnow()
            self.candidates[paper["candidate_id"]]["status"] = "待开考"
            self.candidates[paper["candidate_id"]]["processing"] = _build_processing(
                stage="published",
                status="succeeded",
                progress=100,
                message="考试入口已发布，可直接复制链接与验证码给候选人。",
                step_statuses={
                    "upload": "succeeded",
                    "pdf_parse": "succeeded",
                    "project_extract": "succeeded",
                    "paper_generate": "succeeded",
                    "paper_publish": "succeeded",
                },
            )
        return {
            "paper_id": paper_id,
            "token": token,
            "verification_code": verification_code,
            "exam_url": f"/exam/{token}",
            "access_state": "not_started",
            "duration_minutes": published["duration_minutes"],
        }

    def get_exam_payload(self, token: str) -> dict[str, Any]:
        published = self.exam_tokens.get(token)
        if published is None:
            raise LookupError("Exam token not found.")
        paper = self.papers[published["paper_id"]]
        candidate = self.candidates[published["candidate_id"]]
        session = self.sessions.get(published["session_id"]) if published["session_id"] else None
        payload = {
            "token": token,
            "state": published["access_state"],
            "access_state": published["access_state"],
            "paper_title": paper["title"],
            "candidate_name": candidate["name"],
            "duration_minutes": published["duration_minutes"],
            "heartbeat_interval_ms": HEARTBEAT_INTERVAL_MS,
            "autosave_interval_ms": AUTOSAVE_INTERVAL_MS,
            "risk_events": deepcopy(RISK_EVENT_TYPES),
            "instructions": [
                "请输入验证码进入考试。",
                "系统会自动保存答案，并记录基础风控事件。",
                "交卷后 HR 将查看评分与作答详情。",
            ],
            "started_at": _isoformat(session["started_at"]) if session else None,
            "expires_at": _isoformat(session["expires_at"]) if session else None,
            "submitted_at": _isoformat(session["submitted_at"]) if session else None,
            "last_heartbeat_at": _isoformat(session["last_heartbeat_at"]) if session else None,
            "answers": {
                question_id: deepcopy(item.get("draft_answer", {}))
                for question_id, item in (session["answers"].items() if session else [])
            },
            "submission_summary": None,
            "questions": [],
        }
        if published["access_state"] != "not_started":
            payload["questions"] = [self._serialize_public_question(question) for question in paper["questions"]]
        if session and session["result_id"]:
            payload["result_id"] = session["result_id"]
            result = self.results.get(session["result_id"])
            if result is not None:
                payload["submission_summary"] = {
                    "submitted_at": _isoformat(result["submitted_at"]),
                    "total_score": result["summary"]["total_score"],
                    "objective_score": result["summary"]["objective_score"],
                    "subjective_score": result["summary"]["subjective_score"],
                    "coding_score": result["summary"]["coding_score"],
                }
        return payload

    def start_exam(self, token: str, verification_code: str) -> dict[str, Any]:
        published = self.exam_tokens.get(token)
        if published is None:
            raise LookupError("Exam token not found.")
        if published["verification_code_hash"] != sha256(verification_code.encode("utf-8")).hexdigest():
            raise PermissionError("Verification code is invalid.")
        if published["session_id"]:
            return self._serialize_session(self.sessions[published["session_id"]])
        start_at = _utcnow()
        session_id = self._next_id("session")
        session = {
            "session_id": session_id,
            "token": token,
            "paper_id": published["paper_id"],
            "candidate_id": published["candidate_id"],
            "task_id": published["task_id"],
            "status": "in_progress",
            "started_at": start_at,
            "expires_at": start_at + timedelta(minutes=published["duration_minutes"]),
            "submitted_at": None,
            "last_heartbeat_at": start_at,
            "answers": {},
            "risk_events": [],
            "result_id": None,
        }
        with self._lock:
            self.sessions[session_id] = session
            published["session_id"] = session_id
            published["access_state"] = "in_progress"
            self.candidates[published["candidate_id"]]["status"] = "已开考"
        return self._serialize_session(session)

    def heartbeat(self, token: str) -> dict[str, Any]:
        session = self._require_active_session(token)
        with self._lock:
            session["last_heartbeat_at"] = _utcnow()
        return {
            "token": token,
            "last_heartbeat_at": _isoformat(session["last_heartbeat_at"]),
            "status": "accepted",
        }

    def save_answer(self, token: str, question_id: str, draft_answer: dict[str, Any]) -> dict[str, Any]:
        session = self._require_active_session(token)
        self._get_question(token, question_id)
        snapshot = {
            "draft_answer": deepcopy(draft_answer),
            "last_saved_at": _utcnow(),
            "status": "saved",
        }
        with self._lock:
            answer = session["answers"].setdefault(question_id, {})
            answer.update(snapshot)
        return {
            "token": token,
            "question_id": question_id,
            "draft_answer": deepcopy(draft_answer),
            "last_saved_at": _isoformat(snapshot["last_saved_at"]),
            "status": "saved",
        }

    def record_risk_event(self, token: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._require_active_session(token)
        event = {
            "event_type": event_type,
            "payload": deepcopy(payload),
            "created_at": _utcnow(),
        }
        with self._lock:
            session["risk_events"].append(event)
        return {
            "token": token,
            "event_type": event_type,
            "payload": deepcopy(payload),
            "created_at": _isoformat(event["created_at"]),
        }

    def get_coding_question(self, token: str, question_id: str) -> dict[str, Any]:
        question = self._get_question(token, question_id)
        if question["kind"] != "coding":
            raise ValueError("Coding question not found.")
        return deepcopy(question)

    def store_coding_submission(
        self,
        token: str,
        question_id: str,
        *,
        language: str,
        source_code: str,
        result: dict[str, Any],
    ) -> None:
        session = self._require_active_session(token)
        with self._lock:
            answer = session["answers"].setdefault(question_id, {})
            answer["draft_answer"] = {
                "language": language,
                "source_code": source_code,
            }
            answer["coding_submission"] = deepcopy(result)
            answer["last_saved_at"] = _utcnow()
            answer["status"] = "saved"

    def submit_exam(self, token: str) -> dict[str, Any]:
        session = self._require_active_session(token)
        published = self.exam_tokens[token]
        paper = self.papers[session["paper_id"]]
        answers = session["answers"]
        objective_score = 0
        subjective_score = 0
        coding_score = 0
        reviews = []
        for question in paper["questions"]:
            answer = answers.get(question["id"], {})
            draft_answer = deepcopy(answer.get("draft_answer", {}))
            review = {
                "question_id": question["id"],
                "kind": question["kind"],
                "title": question["title"],
                "max_score": question["score"],
                "draft_answer": draft_answer,
            }
            if question["kind"] == "objective":
                score = score_objective_answer(
                    answer=draft_answer.get("answer", ""),
                    answer_key=question["answer_key"],
                    full_score=question["score"],
                    mode=question["mode"],
                )
                objective_score += score
                review["score"] = score
                review["result"] = "passed" if score else "failed"
            elif question["kind"] == "subjective":
                suggestion = suggest_subjective_score(
                    answer_text=draft_answer.get("answer_text", ""),
                    rubric_text=question["rubric_text"],
                    max_score=question["score"],
                )
                subjective_score += suggestion["suggested_score"]
                review["score"] = suggestion["suggested_score"]
                review["reasoning_summary"] = suggestion["reasoning_summary"]
            elif question["kind"] == "coding":
                submission = answer.get("coding_submission")
                score = submission["summary"]["total_score"] if submission else 0
                coding_score += score
                review["score"] = score
                review["results"] = deepcopy(submission["results"]) if submission else []
            else:
                review["score"] = 0
            reviews.append(review)

        risk_summary = {
            "event_count": len(session["risk_events"]),
            "event_types": dict(Counter(event["event_type"] for event in session["risk_events"])),
        }
        summary = build_score_summary(
            objective_score=objective_score,
            subjective_score=subjective_score,
            coding_score=coding_score,
            risk_summary=risk_summary,
        )
        result_id = self._next_id("result")
        submitted_at = _utcnow()
        result = {
            "result_id": result_id,
            "session_id": session["session_id"],
            "token": token,
            "paper_id": paper["paper_id"],
            "candidate_id": session["candidate_id"],
            "task_id": session["task_id"],
            "status": "completed",
            "submitted_at": submitted_at,
            "summary": summary,
            "question_reviews": reviews,
            "risk_events": deepcopy(session["risk_events"]),
        }
        with self._lock:
            session["status"] = "completed"
            session["submitted_at"] = submitted_at
            session["result_id"] = result_id
            self.results[result_id] = result
            published["access_state"] = "submitted"
            self.candidates[session["candidate_id"]]["status"] = "已完成"
        return {
            "result_id": result_id,
            "session_id": session["session_id"],
            "status": "completed",
            "summary": deepcopy(summary),
            "submitted_at": _isoformat(submitted_at),
        }

    def list_results(self, *, status: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        items = []
        for result in self.results.values():
            if status and result["status"] != status:
                continue
            if task_id and result["task_id"] != task_id:
                continue
            candidate = self.candidates[result["candidate_id"]]
            paper = self.papers[result["paper_id"]]
            items.append(
                {
                    "result_id": result["result_id"],
                    "session_id": result["session_id"],
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["name"],
                    "role": candidate["role"],
                    "paper_id": paper["paper_id"],
                    "paper_title": paper["title"],
                    "task_id": result["task_id"],
                    "status": result["status"],
                    "total_score": result["summary"]["total_score"],
                    "submitted_at": _isoformat(result["submitted_at"]),
                }
            )
        items.sort(key=lambda item: item["submitted_at"] or "", reverse=True)
        return {"items": items, "total": len(items)}

    def get_result(self, result_id: str) -> dict[str, Any]:
        result = self.results.get(result_id)
        if result is None:
            raise LookupError("Result not found.")
        candidate = self.candidates[result["candidate_id"]]
        paper = self.papers[result["paper_id"]]
        return {
            "result_id": result["result_id"],
            "session_id": result["session_id"],
            "status": result["status"],
            "submitted_at": _isoformat(result["submitted_at"]),
            "candidate": self._serialize_candidate_detail(candidate),
            "paper": self._serialize_paper(paper),
            "summary": deepcopy(result["summary"]),
            "answers": deepcopy(result["question_reviews"]),
            "risk_events": [
                {**event, "created_at": _isoformat(event["created_at"])}
                for event in result["risk_events"]
            ],
        }

    def _require_active_session(self, token: str) -> dict[str, Any]:
        published = self.exam_tokens.get(token)
        if published is None:
            raise LookupError("Exam token not found.")
        if not published["session_id"]:
            raise ValueError("Exam has not started.")
        session = self.sessions[published["session_id"]]
        if session["status"] != "in_progress":
            raise ValueError("Exam session is not active.")
        return session

    def _get_question(self, token: str, question_id: str) -> dict[str, Any]:
        published = self.exam_tokens.get(token)
        if published is None:
            raise LookupError("Exam token not found.")
        paper = self.papers[published["paper_id"]]
        for question in paper["questions"]:
            if question["id"] == question_id:
                return question
        raise LookupError("Question not found.")

    def _serialize_task(self, task: dict[str, Any]) -> dict[str, Any]:
        candidate_count = sum(1 for item in self.candidates.values() if item["task_id"] == task["task_id"])
        upload_count = sum(1 for item in self.uploads.values() if item["task_id"] == task["task_id"])
        return {
            "id": task["task_id"],
            "task_id": task["task_id"],
            "title": task["title"],
            "role": task["title"],
            "department": task["department"],
            "city": task["city"],
            "jd_text": task["jd_text"],
            "tags": deepcopy(task["tags"]),
            "template_config": deepcopy(task["template_config"]),
            "duration_minutes": task["duration_minutes"],
            "status": task["status"],
            "candidate_count": candidate_count,
            "upload_count": upload_count,
            "created_at": _isoformat(task["created_at"]),
        }

    def _serialize_upload(self, upload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": upload["upload_id"],
            "upload_id": upload["upload_id"],
            "task_id": upload["task_id"],
            "candidate_id": upload["candidate_id"],
            "file_name": upload["filename"],
            "filename": upload["filename"],
            "status": upload["status"],
            "progress": upload["progress"],
            "created_at": _isoformat(upload["created_at"]),
            "updated_at": _isoformat(upload["updated_at"]),
            "error": upload["error"],
            "processing": deepcopy(upload.get("processing")),
        }

    def _serialize_candidate_card(self, candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": candidate["candidate_id"],
            "task_id": candidate["task_id"],
            "name": candidate["name"],
            "role": candidate["role"],
            "city": candidate["city"],
            "status": candidate["status"],
            "quality": candidate["quality"],
            "summary": candidate["summary"],
            "skills": deepcopy(candidate["skills"]),
            "paper_id": candidate["paper_ids"][-1] if candidate.get("paper_ids") else None,
            "result_id": self._find_candidate_result_id(candidate["candidate_id"]),
            "processing": deepcopy(candidate.get("processing")),
        }

    def _get_candidate_resume_uploaded_at(self, candidate: dict[str, Any]) -> datetime:
        upload_id = candidate.get("latest_upload_id")
        upload = self.uploads.get(upload_id) if upload_id else None
        return upload["created_at"] if upload else candidate["created_at"]

    def _get_candidate_profile_completed_at(self, candidate: dict[str, Any]) -> datetime:
        upload_id = candidate.get("latest_upload_id")
        upload = self.uploads.get(upload_id) if upload_id else None
        return upload["updated_at"] if upload else candidate["created_at"]

    def _serialize_candidate_detail(self, candidate: dict[str, Any]) -> dict[str, Any]:
        if candidate["paper_ids"]:
            next_actions = [{"label": "生成考卷草稿", "target": f"/admin/papers/{candidate['paper_ids'][-1]}"}]
        else:
            next_actions = [
                {
                    "label": "生成考卷草稿",
                    "target": f"/admin/candidates/{candidate['candidate_id']}/papers/generate",
                }
            ]
        next_actions.append(
            {"label": "修正候选人画像", "target": f"/admin/candidates/{candidate['candidate_id']}/edit"}
        )
        return {
            "id": candidate["candidate_id"],
            "task_id": candidate["task_id"],
            "name": candidate["name"],
            "role": candidate["role"],
            "email": candidate["email"],
            "city": candidate["city"],
            "phone": candidate.get("phone", "") or "",
            "status": candidate["status"],
            "quality": candidate["quality"],
            "skills": deepcopy(candidate["skills"]),
            "hobbies": deepcopy(candidate.get("hobbies", [])),
            "height_cm": candidate.get("height_cm"),
            "weight_kg": candidate.get("weight_kg"),
            "available_in_days": candidate.get("available_in_days"),
            "project_summary": candidate["project_summary"],
            "projects": deepcopy(candidate.get("projects", [])),
            "analysis": deepcopy(candidate.get("analysis", {})),
            "processing": deepcopy(candidate.get("processing")),
            "parse_metrics": deepcopy(candidate["parse_metrics"]),
            "review_notes": deepcopy(candidate["review_notes"]),
            "paper_id": candidate["paper_ids"][-1] if candidate.get("paper_ids") else None,
            "invitation_token": self._find_candidate_invitation_token(candidate["candidate_id"]),
            "result_id": self._find_candidate_result_id(candidate["candidate_id"]),
            "next_actions": next_actions,
        }

    def _materialize_question(self, item: dict[str, Any]) -> dict[str, Any]:
        question_id = item["question_id"]
        if item["type"] == "base_info":
            return {
                "id": question_id,
                "kind": "base_info",
                "type": "基础信息",
                "title": item["title"],
                "score": item["score"],
                "description": "请补全个人基础信息，方便 HR 结合岗位需求做后续沟通。",
                "fields": item.get("fields", ["姓名", "手机号", "邮箱", "城市", "可到岗时间"]),
            }
        if item["type"] == "objective":
            detail = OBJECTIVE_DETAILS[question_id]
            return {
                "id": question_id,
                "kind": "objective",
                "type": "客观题",
                "title": item["title"],
                "score": item["score"],
                "description": detail["description"],
                "options": deepcopy(detail["options"]),
                "answer_key": detail["answer_key"],
                "mode": detail["mode"],
            }
        if item["type"] == "subjective":
            detail = SUBJECTIVE_DETAILS.get(
                question_id,
                {
                    "description": item.get("description") or "请结合你的真实项目经历作答。",
                    "rubric_text": item.get("rubric_text") or "项目 技术 取舍 结果 复盘",
                },
            )
            return {
                "id": question_id,
                "kind": "subjective",
                "type": "主观题",
                "title": item["title"],
                "score": item["score"],
                "description": item.get("description") or detail["description"],
                "rubric_text": item.get("rubric_text") or detail["rubric_text"],
            }
        detail = CODING_DETAILS.get(
            question_id,
            {
                "description": item.get("description"),
                "language": item.get("language"),
                "supported_languages": item.get("supported_languages", SUPPORTED_LANGUAGES),
                "starter_code": item.get("starter_code", DEFAULT_STARTER_CODE),
                "testcases": item.get("testcases", DEFAULT_CODING_TESTCASES),
            },
        )
        return {
            "id": question_id,
            "kind": "coding",
            "type": "代码题",
            "title": item["title"],
            "score": item["score"],
            "description": item.get("description") or detail["description"],
            "language": item.get("language") or detail["language"],
            "supported_languages": deepcopy(item.get("supported_languages") or detail["supported_languages"]),
            "starter_code": item.get("starter_code") or detail["starter_code"],
            "testcases": deepcopy(item.get("testcases") or detail["testcases"]),
        }

    def _serialize_paper(self, paper: dict[str, Any]) -> dict[str, Any]:
        invitation = self._find_paper_invitation(paper["paper_id"])
        return {
            "paper_id": paper["paper_id"],
            "candidate_id": paper["candidate_id"],
            "task_id": paper["task_id"],
            "title": paper["title"],
            "mix": deepcopy(paper["mix"]),
            "status": paper["status"],
            "duration_minutes": paper["duration_minutes"],
            "introduction": paper.get("introduction") or "请先完成基础信息，再依次完成客观题、主观题和代码题。",
            "questions": [
                {
                    "id": question["id"],
                    "kind": question["kind"],
                    "type": question["type"],
                    "title": question["title"],
                    "score": question["score"],
                    "description": question["description"],
                    "fields": deepcopy(question.get("fields")),
                    "options": deepcopy(question.get("options")),
                    "answer_key": deepcopy(question.get("answer_key")),
                    "rubric_text": question.get("rubric_text"),
                    "language": question.get("language"),
                    "supported_languages": deepcopy(question.get("supported_languages")),
                    "starter_code": question.get("starter_code"),
                }
                for question in paper["questions"]
            ],
            "generation_summary": deepcopy(paper.get("generation_summary", {})),
            "invitation": invitation,
            "updated_at": _isoformat(paper["updated_at"]),
        }

    def _serialize_public_question(self, question: dict[str, Any]) -> dict[str, Any]:
        short_label = {
            "base_info": "基础信息",
            "objective": "客观题",
            "subjective": "主观题",
            "coding": "代码题",
        }[question["kind"]]
        payload = {
            "id": question["id"],
            "kind": question["kind"],
            "short_label": short_label,
            "type_label": question["type"],
            "title": question["title"],
            "description": question["description"],
            "score": question["score"],
        }
        if question["kind"] == "base_info":
            payload["fields"] = deepcopy(question["fields"])
        elif question["kind"] == "objective":
            payload["options"] = deepcopy(question["options"])
        elif question["kind"] == "coding":
            payload["language"] = question["language"]
            payload["supported_languages"] = deepcopy(question["supported_languages"])
            payload["starter_code"] = question["starter_code"]
        return payload

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "token": session["token"],
            "status": session["status"],
            "started_at": _isoformat(session["started_at"]),
            "expires_at": _isoformat(session["expires_at"]),
        }

    def _find_paper_invitation(self, paper_id: str) -> dict[str, Any] | None:
        for token, published in self.exam_tokens.items():
            if published["paper_id"] == paper_id:
                return {
                    "token": token,
                    "verify_code": published.get("verification_code", ""),
                    "start_url": f"/exam/{token}",
                    "status": published["access_state"],
                }
        return None

    def _find_candidate_invitation_token(self, candidate_id: str) -> str | None:
        for token, published in self.exam_tokens.items():
            if published["candidate_id"] == candidate_id:
                return token
        return None

    def _find_candidate_result_id(self, candidate_id: str) -> str | None:
        for result in self.results.values():
            if result["candidate_id"] == candidate_id:
                return result["result_id"]
        return None


gateway_demo_store = GatewayDemoStore()
