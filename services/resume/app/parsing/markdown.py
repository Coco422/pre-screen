from __future__ import annotations

import re


WATERMARK_TOKEN_RE = re.compile(r"[0-9a-f]{8,}[A-Za-z0-9_-]{12,}~~?", re.IGNORECASE)
SECTION_HEADINGS = (
    "个人信息",
    "教育经历",
    "教育背景",
    "专业技能",
    "相关技能",
    "项目经历",
    "实习经历",
    "竞赛经历",
    "获奖经历",
    "自我评价",
    "个人总结",
)


def clean_resume_text(text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    cleaned_lines: list[str] = []

    for line in text.splitlines():
        original = line
        line = WATERMARK_TOKEN_RE.sub("", line)
        token_removed = original != line
        stripped = _normalize_spaces(line)
        if token_removed:
            warnings.append("removed watermark-like token")
        if not stripped:
            continue
        if _is_probable_watermark_fragment(stripped):
            warnings.append(f"removed watermark-like line: {stripped[:48]}")
            continue
        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip(), _dedupe(warnings)


def build_resume_markdown(
    *,
    title: str,
    pages: list[dict],
    model_markdown: str | None = None,
) -> tuple[str, list[str]]:
    if model_markdown and model_markdown.strip():
        cleaned, warnings = clean_resume_text(model_markdown)
        return cleaned, warnings

    warnings: list[str] = []
    page_blocks = [
        f"# {title}",
        "",
        f"整理说明：本文档按原 {len(pages)} 页页序提取整理。重复水印/哈希标记已从正文中移除，并记录在 metadata 中。",
    ]
    for page in pages:
        page_number = page["page_number"]
        cleaned_text, page_warnings = clean_resume_text(page.get("text", ""))
        warnings.extend([f"page {page_number}: {item}" for item in page_warnings])
        page_title = _page_title(cleaned_text) or "简历内容"
        page_blocks.extend(["", f"## 第 {page_number} 页：{page_title}", ""])
        page_blocks.append(_format_page_body(cleaned_text))

    return "\n".join(page_blocks).strip() + "\n", _dedupe(warnings)


def _format_page_body(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in SECTION_HEADINGS:
            lines.extend(["", f"### {stripped}"])
        else:
            lines.append(stripped)
    return "\n".join(lines).strip()


def _is_probable_watermark_fragment(line: str) -> bool:
    compact = re.sub(r"\s+", "", line)
    if len(compact) < 16:
        return False
    if "@" in compact or "http" in compact.lower():
        return False
    has_watermark_marker = "~~" in compact or "WOW" in compact or "HJ72" in compact
    mostly_ascii = sum(1 for char in compact if ord(char) < 128) / max(len(compact), 1) > 0.9
    return has_watermark_marker and mostly_ascii


def _normalize_spaces(line: str) -> str:
    return re.sub(r"[ \t]+", " ", line).strip()


def _page_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:48]
    return None


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
