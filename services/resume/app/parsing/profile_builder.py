import re


SKILL_PATTERNS = (
    ("Python", r"\bPython\b"),
    ("Vue", r"\bVue(?:\.js)?\b"),
    ("JavaScript", r"\bJavaScript\b|\bJS\b"),
    ("TypeScript", r"\bTypeScript\b|\bTS\b"),
    ("Java", r"(?<![A-Za-z])Java(?!Script)\b"),
    ("C++", r"C\+\+"),
)


def build_candidate_profile(extracted_pages: list[dict], multimodal_pages: list[dict]) -> dict:
    text_blob = "\n".join(page.get("text", "").strip() for page in extracted_pages if page.get("text"))
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text_blob)
    name_match = re.search(r"(?:姓名|Name)[:：]\s*([^\n]+)", text_blob)

    skills: list[str] = []
    for skill, pattern in SKILL_PATTERNS:
        if re.search(pattern, text_blob) and skill not in skills:
            skills.append(skill)

    return {
        "name": name_match.group(1).strip() if name_match else None,
        "email": email_match.group(0) if email_match else None,
        "skills": skills,
        "source_summary": {
            "text_pages": [page["page_number"] for page in extracted_pages],
            "multimodal_pages": [page["page_number"] for page in multimodal_pages],
            "multimodal_summaries": {
                page["page_number"]: page.get("summary", "") for page in multimodal_pages
            },
        },
        "raw_text": text_blob,
    }
