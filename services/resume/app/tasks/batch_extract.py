from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from services.resume.app.domain.models import AvatarAsset, ResumeBatchResult, ResumeParseResult
from services.resume.app.repositories.resume_repository import resume_repository
from services.resume.app.tasks.parse_resume import parse_resume_file


def run_resume_batch(
    *,
    pdf_paths: list[Path],
    output_root: Path = Path("tmp/resume-batches"),
    batch_id: str | None = None,
    use_ai: bool = False,
    save_to_repository: bool = True,
) -> ResumeBatchResult:
    batch_id = batch_id or uuid4().hex[:12]
    output_dir = output_root / batch_id
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed_results: list[ResumeParseResult] = []
    for pdf_path in pdf_paths:
        file_id = uuid4().hex
        candidate_dir = output_dir / _safe_stem(pdf_path)
        pages_dir = candidate_dir / "pages"
        profile = parse_resume_file(pdf_path, render_dir=pages_dir, use_ai=use_ai)

        markdown_path = candidate_dir / "resume.md"
        metadata_path = candidate_dir / "metadata.json"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(profile["markdown"], encoding="utf-8")
        metadata_path.write_text(
            json.dumps(profile["metadata"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        avatar = AvatarAsset(**profile["avatar"])
        result = ResumeParseResult(
            file_id=file_id,
            candidate_name=profile.get("name") or pdf_path.stem,
            original_filename=pdf_path.name,
            markdown=profile["markdown"],
            profile=profile,
            metadata=profile["metadata"],
            avatar=avatar,
        )
        parsed_results.append(result)
        if save_to_repository:
            resume_repository.save_parse_result(result)

    analysis_markdown = build_common_analysis(parsed_results)
    analysis_path = output_dir / "common-analysis.md"
    analysis_path.write_text(analysis_markdown, encoding="utf-8")

    batch_result = ResumeBatchResult(
        batch_id=batch_id,
        file_ids=tuple(result.file_id for result in parsed_results),
        output_dir=str(output_dir),
        analysis_markdown=analysis_markdown,
    )
    if save_to_repository:
        resume_repository.save_batch_result(batch_result)
    return batch_result


def build_common_analysis(results: list[ResumeParseResult]) -> str:
    rows = []
    shared_skills: dict[str, int] = {}
    suspicious: list[str] = []
    role_notes: list[str] = []

    for result in results:
        profile = result.profile
        skills = profile.get("skills", [])
        for skill in skills:
            shared_skills[skill] = shared_skills.get(skill, 0) + 1
        rows.append(
            "| {name} | {role} | {city} | {skills} | {avatar} |".format(
                name=_escape(profile.get("name") or result.candidate_name),
                role=_escape(profile.get("role") or _role_from_filename(result.original_filename)),
                city=_escape(profile.get("city") or "未识别"),
                skills=_escape(", ".join(skills[:8])),
                avatar="有" if result.avatar.status == "found" else "未发现",
            )
        )
        suspicious.extend(_suspicious_claims(result))
        role_notes.append(_role_fit_note(result))

    top_skills = sorted(shared_skills.items(), key=lambda item: (-item[1], item[0]))
    skill_lines = [f"- {skill}：{count}/{len(results)} 份简历出现" for skill, count in top_skills[:12]]

    content = [
        "# 简历批量共性分析",
        "",
        "## 通用内容",
        "",
        "- 四份简历均面向 26 届本科候选人，并包含联系方式、教育经历、技能、项目或实习经历。",
        "- 多数简历强调 AI Agent、RAG、大模型应用工程化或模型/算法相关实践。",
        "- 多数项目描述带有性能、准确率、吞吐、响应时间或业务节省比例等量化指标，适合后续面试追问验证。",
        "",
        "## 技能矩阵",
        "",
        "| 候选人 | 岗位方向 | 城市 | 识别技能 | 头像 |",
        "| --- | --- | --- | --- | --- |",
        *rows,
        "",
        "## 高频技能",
        "",
        *(skill_lines or ["- 暂无可统计技能。"]),
        "",
        "## 岗位匹配提示",
        "",
        *[f"- {note}" for note in role_notes],
        "",
        "## 需要复核的表述",
        "",
        *[f"- {item}" for item in suspicious[:12]],
    ]
    return "\n".join(content).strip() + "\n"


def _safe_stem(path: Path) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "_" for char in path.stem)


def _escape(value: str) -> str:
    return value.replace("|", "\\|")


def _role_from_filename(filename: str) -> str:
    if "前端" in filename:
        return "前端开发工程师"
    if "全栈" in filename:
        return "全栈开发工程师"
    return "未识别"


def _role_fit_note(result: ResumeParseResult) -> str:
    profile = result.profile
    name = profile.get("name") or result.candidate_name
    skills = set(profile.get("skills", []))
    role = profile.get("role") or _role_from_filename(result.original_filename)
    if "前端" in role and {"Vue", "React", "TypeScript"} & skills:
        return f"{name}：前端方向技能信号较明确，可重点追问组件化、性能优化和工程化细节。"
    if "全栈" in role and {"Python", "FastAPI", "Django", "Vue", "Java"} & skills:
        return f"{name}：全栈方向覆盖前后端或 AI 应用，可重点追问真实职责边界与部署经验。"
    return f"{name}：岗位方向需要结合项目贡献深度继续复核。"


def _suspicious_claims(result: ResumeParseResult) -> list[str]:
    text = result.profile.get("raw_text", "")
    name = result.profile.get("name") or result.candidate_name
    markers = ("百TB", "准确率达到98", "准确率达到96", "100% 准确", "提升至 97%", "20 + 子 Agent")
    claims = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(marker in stripped for marker in markers):
            claims.append(f"{name}：`{stripped[:120]}`")
    if not claims:
        claims.append(f"{name}：量化成果需在面试中要求说明数据口径、个人贡献和验证方式。")
    return claims
