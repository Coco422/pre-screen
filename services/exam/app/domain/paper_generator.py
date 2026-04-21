from __future__ import annotations

from collections import Counter
from typing import Any, Sequence


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

OBJECTIVE_BANK = [
    {
        "question_id": "obj-vue-reactivity",
        "type": "objective",
        "title": "Vue 响应式原理基础",
        "score": 5,
        "tags": ("Vue", "frontend", "响应式"),
    },
    {
        "question_id": "obj-typescript-types",
        "type": "objective",
        "title": "TypeScript 类型系统",
        "score": 5,
        "tags": ("TypeScript", "frontend"),
    },
    {
        "question_id": "obj-engineering-build",
        "type": "objective",
        "title": "前端工程化基础",
        "score": 5,
        "tags": ("工程化", "frontend", "Vite"),
    },
    {
        "question_id": "obj-browser-network",
        "type": "objective",
        "title": "浏览器与网络基础",
        "score": 5,
        "tags": ("浏览器", "网络", "frontend"),
    },
    {
        "question_id": "obj-javascript-runtime",
        "type": "objective",
        "title": "JavaScript 运行时机制",
        "score": 5,
        "tags": ("JavaScript", "frontend"),
    },
    {
        "question_id": "obj-rest-idempotency",
        "type": "objective",
        "title": "接口幂等与状态设计",
        "score": 5,
        "tags": ("REST", "后端", "接口"),
    },
    {
        "question_id": "obj-rag-retrieval",
        "type": "objective",
        "title": "RAG 检索链路基础",
        "score": 5,
        "tags": ("RAG", "检索", "AI"),
    },
    {
        "question_id": "obj-auth-session",
        "type": "objective",
        "title": "鉴权与会话刷新",
        "score": 5,
        "tags": ("权限控制", "Token", "接口"),
    },
]

CODING_TEMPLATES = {
    "notification_dedupe": {
        "title": "实现告警通知去重",
        "description": "请从标准输入读取一个 JSON 数组，输出按原顺序稳定去重后的结果，用于模拟告警风暴去重。",
        "testcases": [
            {"stdin": "[1,1,2,3,2]\n", "expected_stdout": "[1,2,3]\n", "score": 50},
            {"stdin": "[\"a\",\"a\",\"b\",\"c\",\"b\"]\n", "expected_stdout": "[\"a\",\"b\",\"c\"]\n", "score": 50},
        ],
    },
    "permission_routes": {
        "title": "实现权限路由过滤",
        "description": (
            "请从标准输入读取一个 JSON 对象，格式为 "
            "{\"menu\":[{\"name\":\"dashboard\",\"permission\":\"view_dashboard\"}],\"granted\":[\"view_dashboard\"]}。"
            "输出一个 JSON 数组，内容为当前用户可见的菜单 name，顺序与输入保持一致。"
        ),
        "testcases": [
            {
                "stdin": "{\"menu\":[{\"name\":\"dashboard\",\"permission\":\"view_dashboard\"},{\"name\":\"users\",\"permission\":\"view_users\"}],\"granted\":[\"view_dashboard\"]}\n",
                "expected_stdout": "[\"dashboard\"]\n",
                "score": 50,
            },
            {
                "stdin": "{\"menu\":[{\"name\":\"orders\",\"permission\":\"view_orders\"},{\"name\":\"finance\",\"permission\":\"view_finance\"}],\"granted\":[\"view_finance\",\"view_orders\"]}\n",
                "expected_stdout": "[\"orders\",\"finance\"]\n",
                "score": 50,
            },
        ],
    },
    "log_aggregation": {
        "title": "实现接口日志聚合",
        "description": (
            "请从标准输入读取一个 JSON 数组，数组元素为接口路径字符串。"
            "输出一个 JSON 对象，按接口路径统计出现次数，key 按字母序排序。"
        ),
        "testcases": [
            {
                "stdin": "[\"/api/login\",\"/api/login\",\"/api/profile\"]\n",
                "expected_stdout": "{\"/api/login\":2,\"/api/profile\":1}\n",
                "score": 50,
            },
            {
                "stdin": "[\"/exam/start\",\"/exam/submit\",\"/exam/start\"]\n",
                "expected_stdout": "{\"/exam/start\":2,\"/exam/submit\":1}\n",
                "score": 50,
            },
        ],
    },
    "rag_merge": {
        "title": "实现 RAG 召回结果去重归并",
        "description": (
            "请从标准输入读取一个 JSON 数组，数组元素为文档 id 字符串。"
            "输出一个 JSON 数组，对文档 id 做稳定去重，用于模拟多路召回后的结果归并。"
        ),
        "testcases": [
            {
                "stdin": "[\"doc-1\",\"doc-2\",\"doc-1\",\"doc-3\"]\n",
                "expected_stdout": "[\"doc-1\",\"doc-2\",\"doc-3\"]\n",
                "score": 50,
            },
            {
                "stdin": "[\"faq-9\",\"faq-9\",\"kb-1\"]\n",
                "expected_stdout": "[\"faq-9\",\"kb-1\"]\n",
                "score": 50,
            },
        ],
    },
}


def _score_question(item: dict[str, Any], signals: set[str], jd_text: str) -> tuple[int, int]:
    jd_lower = jd_text.lower()
    score = 0
    for tag in item.get("tags", ()):
        tag_lower = str(tag).lower()
        if tag in signals or tag_lower in signals:
            score += 3
        if tag_lower in jd_lower:
            score += 2
    return score, -len(item["question_id"])


def _pick_questions(bank: list[dict[str, Any]], count: int, signals: set[str], jd_text: str) -> list[dict[str, Any]]:
    ranked = sorted(
        bank,
        key=lambda item: (_score_question(item, signals, jd_text), item["question_id"]),
        reverse=True,
    )
    return ranked[:count]


def _build_base_info_questions(count: int) -> list[dict[str, Any]]:
    base_fields = ["姓名", "手机号", "邮箱", "城市", "身高", "体重", "爱好", "可到岗时间"]
    questions: list[dict[str, Any]] = []
    for index in range(count):
        title = "补充基础信息" if index == 0 else f"补充基础信息（扩展 {index}）"
        questions.append(
            {
                "question_id": f"base-info-{index + 1}",
                "type": "base_info",
                "title": title,
                "score": 0,
                "fields": base_fields,
            }
        )
    return questions


def _build_subjective_questions(
    count: int,
    *,
    candidate_profile: dict[str, Any],
    question_brief: dict[str, Any],
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for index, item in enumerate(question_brief.get("subjective_questions", []), start=1):
        questions.append(
            {
                "question_id": f"subjective-brief-{index}",
                "type": "subjective",
                "title": item["title"],
                "score": int(item.get("score") or 20),
                "description": item["description"],
                "rubric_text": item["rubric_text"],
            }
        )
        if len(questions) >= count:
            return questions

    projects = candidate_profile.get("projects") or []
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            project = {"name": str(project), "role": ""}
        questions.append(
            {
                "question_id": f"subjective-project-{index}",
                "type": "subjective",
                "title": f"围绕「{project['name']}」复盘一次关键实现",
                "score": 20,
                "description": (
                    f"请结合你在「{project['name']}」中的真实角色与职责，说明最难的一段实现、"
                    "当时的约束、你的取舍，以及最后如何验证结果。"
                ),
                "rubric_text": "项目 角色 约束 取舍 验证 复盘",
            }
        )
        if len(questions) >= count:
            return questions

    while len(questions) < count:
        questions.append(
            {
                "question_id": f"subjective-generic-{len(questions) + 1}",
                "type": "subjective",
                "title": "描述一次你定位复杂问题并推动落地的过程",
                "score": 15,
                "description": "请说明问题背景、定位过程、如何验证修复以及事后复盘。",
                "rubric_text": "问题 定位 数据 方案 验证 复盘",
            }
        )
    return questions


def _build_coding_questions(
    count: int,
    *,
    candidate_profile: dict[str, Any],
    question_brief: dict[str, Any],
) -> list[dict[str, Any]]:
    if count <= 0:
        return []
    theme = str(question_brief.get("coding_theme") or "notification_dedupe")
    if theme not in CODING_TEMPLATES:
        theme = "notification_dedupe"
    template = CODING_TEMPLATES[theme]
    project_name = ""
    if candidate_profile.get("projects"):
        first_project = candidate_profile["projects"][0]
        project_name = first_project["name"] if isinstance(first_project, dict) else str(first_project)
    language = _choose_coding_language(
        question_brief.get("coding_language"),
        candidate_profile.get("recommended_languages", []),
        candidate_profile.get("skills", []),
    )
    project_prefix = f"结合你在「{project_name}」中的经验，" if project_name else ""
    return [
        {
            "question_id": f"coding-{theme}-{language.lower()}",
            "type": "coding",
            "title": template["title"],
            "score": 50,
            "description": project_prefix + template["description"],
            "language": language,
            "supported_languages": SUPPORTED_LANGUAGES,
            "starter_code": _build_starter_code(language, theme),
            "testcases": template["testcases"],
        }
        for _ in range(count)
    ]


def _choose_coding_language(explicit: str | None, recommended: Sequence[str], skills: Sequence[str]) -> str:
    candidates = [explicit, *recommended, *skills, "JavaScript", "Python"]
    for candidate in candidates:
        if candidate in SUPPORTED_LANGUAGES:
            return str(candidate)
    return "JavaScript"


def _build_starter_code(language: str, theme: str) -> str:
    function_name = {
        "notification_dedupe": "solve",
        "permission_routes": "solve",
        "log_aggregation": "solve",
        "rag_merge": "solve",
    }[theme]
    starters = {
        "JavaScript": f"function {function_name}(input) {{\n  return input;\n}}\n",
        "TypeScript": f"function {function_name}(input: unknown): unknown {{\n  return input;\n}}\n",
        "Python": f"def {function_name}(payload):\n    return payload\n",
        "Java": (
            "import java.util.*;\n\n"
            "class Main {\n"
            f"    static Object {function_name}(Object payload) {{\n"
            "        return payload;\n"
            "    }\n"
            "}\n"
        ),
        "C": "/* 从标准输入读取 JSON 文本并输出结果 */\n",
        "C++": "#include <bits/stdc++.h>\nusing namespace std;\nint main() {\n    return 0;\n}\n",
        "Go": "package main\n\nfunc main() {\n}\n",
        "Rust": "fn main() {\n}\n",
    }
    return starters.get(language, starters["JavaScript"])


def _collect_signals(candidate_profile: dict[str, Any], question_brief: dict[str, Any], template_tags: Sequence[str]) -> set[str]:
    signals = {str(item) for item in [*candidate_profile.get("skills", []), *template_tags]}
    for project in candidate_profile.get("projects", []):
        if isinstance(project, dict):
            for item in project.get("tech_stack", []):
                signals.add(str(item))
            if project.get("name"):
                signals.add(str(project["name"]))
        else:
            signals.add(str(project))
    for topic in question_brief.get("focus_topics", []):
        signals.add(str(topic))
        signals.add(str(topic).lower())
    return signals


def generate_paper_draft(job_template: dict[str, Any], jd_text: str, candidate_profile: dict[str, Any]) -> dict[str, Any]:
    objective_count = job_template["objective_count"]
    subjective_count = job_template["subjective_count"]
    coding_count = job_template["coding_count"]
    base_info_count = job_template.get("base_info_count", 1)

    template_tags = job_template.get("tags", [])
    question_brief = candidate_profile.get("question_brief") or {}
    signals = _collect_signals(candidate_profile, question_brief, template_tags)

    questions = _build_base_info_questions(base_info_count)
    questions.extend(_pick_questions(OBJECTIVE_BANK, objective_count, signals, jd_text))
    questions.extend(
        _build_subjective_questions(
            subjective_count,
            candidate_profile=candidate_profile,
            question_brief=question_brief,
        )
    )
    questions.extend(
        _build_coding_questions(
            coding_count,
            candidate_profile=candidate_profile,
            question_brief=question_brief,
        )
    )

    question_mix = Counter(question["type"] for question in questions)
    matched_projects = [
        project["name"] if isinstance(project, dict) else str(project)
        for project in candidate_profile.get("projects", [])[:3]
    ]
    focus_topics = list(dict.fromkeys([*question_brief.get("focus_topics", []), *candidate_profile.get("focus_topics", [])]))[:6]
    return {
        "template_name": job_template["name"],
        "question_mix": dict(question_mix),
        "questions": questions,
        "prompt_version": "paper-draft/v1",
        "jd_summary": jd_text[:160],
        "candidate_signals": list(signals)[:10],
        "question_type_counts": dict(question_mix),
        "introduction": question_brief.get("introduction")
        or "本套测评会先补充基础信息，再围绕你的项目经历、岗位能力和代码能力进行筛查。",
        "generation_summary": {
            "matched_projects": matched_projects,
            "focus_topics": focus_topics,
            "generation_notes": question_brief.get("generation_notes", []),
            "coding_theme": question_brief.get("coding_theme") or "notification_dedupe",
            "coding_language": _choose_coding_language(
                question_brief.get("coding_language"),
                candidate_profile.get("recommended_languages", []),
                candidate_profile.get("skills", []),
            ),
        },
    }
