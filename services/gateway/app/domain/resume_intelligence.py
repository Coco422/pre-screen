from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Sequence

from pre_screen_common.ai_client import AIClient

SUPPORTED_CODING_LANGUAGES = [
    "C",
    "C++",
    "Java",
    "Python",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
]

RESUME_SYSTEM_PROMPT = """
你是一名严谨的招聘分析助手。你会读取候选人简历文本，以及必要时附带的 PDF 页面截图。
你的任务不是写花哨摘要，而是为后续出题生成结构化候选人画像。

要求：
1. 只输出 JSON，不要输出 markdown，不要输出额外说明。
2. 项目经历必须尽量结构化，tech_stack / responsibilities / achievements / metrics 都输出数组。
3. focus_topics 用来指导后续出题，必须是 3-6 个具体方向，例如“权限控制”“RAG 检索”“异步任务”“接口联调”。
4. recommended_languages 只能从这些语言里选：C、C++、Java、Python、JavaScript、TypeScript、Go、Rust。
5. 如果没有明确证据，不要编造；缺失字段可以留空或 null。
""".strip()

QUESTION_SYSTEM_PROMPT = """
你是一名招聘试卷设计助手。请根据岗位要求和候选人的项目经历，输出一份“出题 brief”。

要求：
1. 只输出 JSON，不要输出 markdown。
2. 题目必须优先绑定候选人的真实项目与职责，避免泛泛而谈。
3. subjective_questions 最多输出 2 题，必须能直接拿去渲染为主观题。
4. coding_theme 只能从这些主题里选一个：notification_dedupe、permission_routes、log_aggregation、rag_merge。
5. coding_language 只能从这些语言里选：C、C++、Java、Python、JavaScript、TypeScript、Go、Rust。
""".strip()


def enrich_resume_profile(parsed_profile: dict[str, Any], image_paths: Sequence[Path] | None = None) -> dict[str, Any]:
    client = _build_ai_client()
    if client is not None:
        try:
            return _normalize_resume_profile(
                client.json_completion(
                    system_prompt=RESUME_SYSTEM_PROMPT,
                    user_prompt=_build_resume_prompt(parsed_profile),
                    images=list(image_paths or [])[:3],
                    temperature=0.1,
                )
            )
        except Exception:
            pass
    return _fallback_resume_profile(parsed_profile)


def build_question_brief(
    *,
    candidate_profile: dict[str, Any],
    job_context: dict[str, Any],
) -> dict[str, Any]:
    client = _build_ai_client()
    if client is not None:
        try:
            return _normalize_question_brief(
                client.json_completion(
                    system_prompt=QUESTION_SYSTEM_PROMPT,
                    user_prompt=_build_question_prompt(candidate_profile, job_context),
                    temperature=0.15,
                )
            )
        except Exception:
            pass
    return _fallback_question_brief(candidate_profile=candidate_profile, job_context=job_context)


def _build_ai_client() -> AIClient | None:
    api_key = os.environ.get("AI_API_KEY")
    base_url = os.environ.get("AI_BASE_URL")
    model = os.environ.get("AI_MODEL")
    if not api_key or not base_url or not model:
        return None
    return AIClient(api_key=api_key, base_url=base_url, model=model)


def _build_resume_prompt(parsed_profile: dict[str, Any]) -> str:
    raw_text = (parsed_profile.get("raw_text") or "").strip()
    raw_text = raw_text[:14_000]
    page_metrics = parsed_profile.get("page_metrics", [])
    multimodal_pages = parsed_profile.get("source_summary", {}).get("multimodal_pages", [])
    return f"""
请根据下面的简历文本和页面提示，输出一个 JSON 对象，字段如下：
{{
  "display_name": "候选人姓名或 null",
  "email": "邮箱或 null",
  "phone": "手机号或 null",
  "city": "城市或 null",
  "skills": ["技能1", "技能2"],
  "hobbies": ["爱好1"],
  "profile_summary": "2-3 句浓缩画像",
  "project_summary": "1 段项目摘要",
  "strengths": ["亮点1", "亮点2"],
  "risks": ["风险1"],
  "focus_topics": ["后续出题方向1", "方向2"],
  "recommended_languages": ["Python", "JavaScript"],
  "missing_fields": ["身高", "体重"],
  "projects": [
    {{
      "project_id": "proj-1",
      "name": "项目名",
      "role": "本人角色",
      "summary": "项目概述",
      "tech_stack": ["Vue3", "FastAPI"],
      "responsibilities": ["职责1", "职责2"],
      "achievements": ["结果1"],
      "metrics": ["指标1"],
      "source_pages": [1, 2],
      "confidence": "high|medium|low"
    }}
  ]
}}

页面指标：
{page_metrics}

低文本/需补读页：
{multimodal_pages}

简历文本：
{raw_text}
""".strip()


def _build_question_prompt(candidate_profile: dict[str, Any], job_context: dict[str, Any]) -> str:
    projects = candidate_profile.get("projects", [])[:3]
    return f"""
请根据以下岗位与候选人项目经历，输出一份结构化出题 brief JSON：
{{
  "introduction": "给候选人的开场说明",
  "focus_topics": ["重点能力1", "重点能力2"],
  "subjective_questions": [
    {{
      "title": "主观题标题",
      "description": "必须强绑定候选人某个项目或职责",
      "rubric_text": "评分关注关键词",
      "score": 20
    }}
  ],
  "coding_theme": "notification_dedupe|permission_routes|log_aggregation|rag_merge",
  "coding_language": "Python|JavaScript|Java|C++|C|TypeScript|Go|Rust",
  "generation_notes": ["本次为何这样出题"]
}}

岗位上下文：
{job_context}

候选人结构化画像：
{{
  "skills": {candidate_profile.get("skills", [])},
  "focus_topics": {candidate_profile.get("focus_topics", [])},
  "recommended_languages": {candidate_profile.get("recommended_languages", [])},
  "project_summary": {candidate_profile.get("project_summary", "")!r},
  "projects": {projects}
}}
""".strip()


def _normalize_resume_profile(payload: dict[str, Any]) -> dict[str, Any]:
    projects: list[dict[str, Any]] = []
    for index, project in enumerate(payload.get("projects") or [], start=1):
        if not isinstance(project, dict):
            continue
        projects.append(
            {
                "project_id": str(project.get("project_id") or f"proj-{index}"),
                "name": str(project.get("name") or f"项目 {index}"),
                "role": str(project.get("role") or ""),
                "summary": str(project.get("summary") or ""),
                "tech_stack": _coerce_string_list(project.get("tech_stack")),
                "responsibilities": _coerce_string_list(project.get("responsibilities")),
                "achievements": _coerce_string_list(project.get("achievements")),
                "metrics": _coerce_string_list(project.get("metrics")),
                "source_pages": _coerce_int_list(project.get("source_pages")),
                "confidence": _coerce_confidence(project.get("confidence")),
            }
        )

    recommended_languages = []
    for language in _coerce_string_list(payload.get("recommended_languages")):
        normalized = _normalize_language_name(language)
        if normalized in SUPPORTED_CODING_LANGUAGES and normalized not in recommended_languages:
            recommended_languages.append(normalized)

    return {
        "display_name": _clean_scalar(payload.get("display_name")),
        "email": _clean_scalar(payload.get("email")),
        "phone": _clean_scalar(payload.get("phone")),
        "city": _clean_scalar(payload.get("city")),
        "skills": _coerce_string_list(payload.get("skills")),
        "hobbies": _coerce_string_list(payload.get("hobbies")),
        "profile_summary": _clean_scalar(payload.get("profile_summary")) or "已完成简历解析，等待 HR 复核。",
        "project_summary": _clean_scalar(payload.get("project_summary")) or "已完成项目经历整理。",
        "strengths": _coerce_string_list(payload.get("strengths")),
        "risks": _coerce_string_list(payload.get("risks")),
        "focus_topics": _coerce_string_list(payload.get("focus_topics")),
        "recommended_languages": recommended_languages or ["JavaScript", "Python"],
        "missing_fields": _coerce_string_list(payload.get("missing_fields")),
        "projects": projects,
    }


def _normalize_question_brief(payload: dict[str, Any]) -> dict[str, Any]:
    subjective_questions = []
    for item in payload.get("subjective_questions") or []:
        if not isinstance(item, dict):
            continue
        subjective_questions.append(
            {
                "title": str(item.get("title") or "结合你的项目经历说明一次关键取舍"),
                "description": str(item.get("description") or "请结合你在项目中的真实职责进行作答。"),
                "rubric_text": str(item.get("rubric_text") or "项目 技术 取舍 结果 复盘"),
                "score": int(item.get("score") or 20),
            }
        )

    coding_theme = str(payload.get("coding_theme") or "notification_dedupe")
    if coding_theme not in {"notification_dedupe", "permission_routes", "log_aggregation", "rag_merge"}:
        coding_theme = "notification_dedupe"

    coding_language = _normalize_language_name(payload.get("coding_language"))
    if coding_language not in SUPPORTED_CODING_LANGUAGES:
        coding_language = "JavaScript"

    return {
        "introduction": str(payload.get("introduction") or "本套测评会结合你的项目经历与岗位要求进行提问。"),
        "focus_topics": _coerce_string_list(payload.get("focus_topics")),
        "subjective_questions": subjective_questions[:2],
        "coding_theme": coding_theme,
        "coding_language": coding_language,
        "generation_notes": _coerce_string_list(payload.get("generation_notes")),
    }


def _fallback_resume_profile(parsed_profile: dict[str, Any]) -> dict[str, Any]:
    raw_text = (parsed_profile.get("raw_text") or "").strip()
    phone_match = re.search(r"1\d{10}", raw_text)
    city_match = re.search(r"(深圳|广州|上海|北京|杭州|成都|武汉|南京|苏州|西安)", raw_text)
    projects = _extract_projects_from_text(raw_text)
    focus_topics = _build_focus_topics(parsed_profile.get("skills", []), projects)
    return {
        "display_name": parsed_profile.get("name"),
        "email": parsed_profile.get("email"),
        "phone": phone_match.group(0) if phone_match else None,
        "city": city_match.group(1) if city_match else None,
        "skills": _coerce_string_list(parsed_profile.get("skills")),
        "hobbies": [],
        "profile_summary": "已基于文本层完成候选人画像整理，可继续人工复核。",
        "project_summary": _build_project_summary(projects, raw_text),
        "strengths": [f"简历中出现 {skill}" for skill in _coerce_string_list(parsed_profile.get("skills"))[:3]],
        "risks": ["项目指标未完全量化"] if not projects else [],
        "focus_topics": focus_topics,
        "recommended_languages": _recommend_languages(parsed_profile.get("skills", [])),
        "missing_fields": ["身高", "体重", "爱好"],
        "projects": projects,
    }


def _fallback_question_brief(
    *,
    candidate_profile: dict[str, Any],
    job_context: dict[str, Any],
) -> dict[str, Any]:
    projects = candidate_profile.get("projects") or []
    project_name = projects[0]["name"] if projects else "你最近的项目"
    preferred_languages = candidate_profile.get("recommended_languages") or ["JavaScript", "Python"]
    skills = candidate_profile.get("skills") or []
    focus_topics = list(dict.fromkeys([*candidate_profile.get("focus_topics", []), *skills]))[:4]

    coding_theme = "notification_dedupe"
    if any("RAG" in topic.upper() for topic in focus_topics):
        coding_theme = "rag_merge"
    elif any("权限" in topic for topic in focus_topics):
        coding_theme = "permission_routes"
    elif any("日志" in topic or "接口" in topic for topic in focus_topics):
        coding_theme = "log_aggregation"

    return {
        "introduction": f"本套测评会结合你在「{project_name}」等项目中的真实职责进行提问。",
        "focus_topics": focus_topics,
        "subjective_questions": [
            {
                "title": f"围绕「{project_name}」说明一次关键技术取舍",
                "description": "请讲清楚你负责的模块、当时的约束条件、做出的技术决策和最终结果。",
                "rubric_text": "项目 角色 约束 取舍 验证 复盘",
                "score": 20,
            }
        ],
        "coding_theme": coding_theme,
        "coding_language": preferred_languages[0],
        "generation_notes": [f"题目围绕候选人的项目「{project_name}」展开。"],
    }


def _extract_projects_from_text(raw_text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    projects: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if not any(keyword in line for keyword in ("项目", "系统", "平台", "知识库", "助教")):
            continue
        window = " ".join(lines[index : index + 4])
        if len(window) < 12:
            continue
        projects.append(
            {
                "project_id": f"proj-{len(projects) + 1}",
                "name": line[:40],
                "role": "",
                "summary": window[:160],
                "tech_stack": _extract_keywords(window),
                "responsibilities": [],
                "achievements": [],
                "metrics": [],
                "source_pages": [],
                "confidence": "medium",
            }
        )
        if len(projects) >= 3:
            break
    return projects


def _extract_keywords(text: str) -> list[str]:
    keywords = []
    for word in ["Vue", "Vue3", "TypeScript", "JavaScript", "Python", "Java", "FastAPI", "RAG", "LangChain", "Chroma", "Pinia", "Axios"]:
        if word.lower() in text.lower() and word not in keywords:
            keywords.append(word)
    return keywords


def _build_focus_topics(skills: Sequence[str], projects: Sequence[dict[str, Any]]) -> list[str]:
    topics = []
    for project in projects:
        for tag in project.get("tech_stack", []):
            if tag not in topics:
                topics.append(tag)
    for skill in skills:
        if skill not in topics:
            topics.append(str(skill))
    return topics[:5] or ["项目复盘", "技术取舍", "接口联调"]


def _build_project_summary(projects: Sequence[dict[str, Any]], raw_text: str) -> str:
    if projects:
        names = "、".join(project["name"] for project in projects[:2])
        return f"已识别到 {names} 等项目，适合围绕职责边界、技术取舍与问题排查出题。"
    return raw_text[:160] or "解析中，暂无项目摘要。"


def _recommend_languages(skills: Sequence[str]) -> list[str]:
    ordered = []
    for language in SUPPORTED_CODING_LANGUAGES:
        if any(str(skill).lower() == language.lower() for skill in skills):
            ordered.append(language)
    if not ordered:
        ordered = ["JavaScript", "Python"]
    return ordered[:3]


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        text = _clean_scalar(item)
        if text and text not in items:
            items.append(text)
    return items


def _coerce_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        try:
            items.append(int(item))
        except (TypeError, ValueError):
            continue
    return items


def _coerce_confidence(value: Any) -> str:
    text = str(value or "medium").lower()
    if text not in {"high", "medium", "low"}:
        return "medium"
    return text


def _normalize_language_name(value: Any) -> str:
    aliases = {
        "c": "C",
        "c++": "C++",
        "cpp": "C++",
        "java": "Java",
        "python": "Python",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "typescript": "TypeScript",
        "ts": "TypeScript",
        "go": "Go",
        "rust": "Rust",
    }
    key = str(value or "").strip().lower()
    return aliases.get(key, str(value or "").strip())


def _clean_scalar(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
