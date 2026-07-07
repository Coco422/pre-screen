import re


SKILL_PATTERNS = (
    ("Python", r"(?<![A-Za-z])Python(?![A-Za-z])"),
    ("FastAPI", r"(?<![A-Za-z])FastAPI(?![A-Za-z])"),
    ("Django", r"(?<![A-Za-z])Django(?![A-Za-z])"),
    ("Vue", r"(?<![A-Za-z])Vue(?:\.js)?(?![A-Za-z])"),
    ("React", r"(?<![A-Za-z])React(?:18|19)?(?![A-Za-z])"),
    ("JavaScript", r"(?<![A-Za-z])JavaScript(?![A-Za-z])|(?<![A-Za-z])JS(?![A-Za-z])"),
    ("TypeScript", r"(?<![A-Za-z])TypeScript(?![A-Za-z])|(?<![A-Za-z])TS(?![A-Za-z])"),
    ("Java", r"(?<![A-Za-z])Java(?!Script)\b"),
    ("C++", r"C\+\+"),
    ("Spring Boot", r"(?<![A-Za-z])Spring\s*Boot(?![A-Za-z])"),
    ("MySQL", r"(?<![A-Za-z])MySQL(?![A-Za-z])"),
    ("Redis", r"(?<![A-Za-z])Redis(?![A-Za-z])"),
    ("Docker", r"(?<![A-Za-z])Docker(?![A-Za-z])"),
    ("LangGraph", r"(?<![A-Za-z])LangGraph(?![A-Za-z])"),
    ("LangChain", r"(?<![A-Za-z])LangChain(?![A-Za-z])"),
    ("RAG", r"(?<![A-Za-z])RAG(?![A-Za-z])|GraphRAG"),
    ("Agent", r"(?<![A-Za-z])Agent(?![A-Za-z])|智能体|多 Agent"),
    ("PyTorch", r"(?<![A-Za-z])PyTorch(?![A-Za-z])"),
    ("OpenCV", r"(?<![A-Za-z])OpenCV(?![A-Za-z])"),
)

PHONE_PATTERN = re.compile(r"(?<!\d)(1\d{10})(?!\d)")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
NAME_PATTERN = re.compile(r"(?:姓名|Name)\s*[:：]\s*([^\n\r]+)")
ROLE_PATTERN = re.compile(
    r"(前端开发(?:工程师|实习生)?|全栈(?:工程师|开发工程师)?|Java后端开发|后端开发(?:工程师)?)"
)
CITY_PATTERN = re.compile(r"(深圳|广州|杭州|上海|北京|成都|武汉|南京|长沙)")


def build_candidate_profile(
    extracted_pages: list[dict],
    multimodal_pages: list[dict],
    model_profile: dict | None = None,
) -> dict:
    text_blob = "\n".join(page.get("text", "").strip() for page in extracted_pages if page.get("text"))
    email_match = EMAIL_PATTERN.search(text_blob)
    phone_match = PHONE_PATTERN.search(text_blob)
    name_match = NAME_PATTERN.search(text_blob)
    role_match = ROLE_PATTERN.search(text_blob)
    city_match = CITY_PATTERN.search(text_blob)

    skills: list[str] = []
    for skill, pattern in SKILL_PATTERNS:
        if re.search(pattern, text_blob) and skill not in skills:
            skills.append(skill)

    detected_name = name_match.group(1).strip() if name_match else _first_name_like_line(text_blob)
    profile = {
        "name": detected_name if _looks_like_name(detected_name) else None,
        "phone": phone_match.group(1) if phone_match else None,
        "email": email_match.group(0) if email_match else None,
        "role": role_match.group(1) if role_match else None,
        "city": city_match.group(1) if city_match else None,
        "skills": skills,
        "summary": _summary_from_text(text_blob),
        "source_summary": {
            "text_pages": [page["page_number"] for page in extracted_pages],
            "multimodal_pages": [page["page_number"] for page in multimodal_pages],
            "multimodal_summaries": {
                page["page_number"]: page.get("summary", "") for page in multimodal_pages
            },
        },
        "raw_text": text_blob,
    }
    if model_profile:
        profile = _merge_model_profile(profile, model_profile)
    return profile


def _first_name_like_line(text: str) -> str | None:
    for line in text.splitlines()[:12]:
        stripped = line.strip()
        if not stripped:
            continue
        if "简历" in stripped:
            stripped = stripped.replace("简历", "").strip()
        if 2 <= len(stripped) <= 8 and not any(char.isdigit() for char in stripped):
            return stripped if _looks_like_name(stripped) else None
    return None


def _looks_like_name(value: str | None) -> bool:
    if not value:
        return False
    compact = value.replace(" ", "")
    if not compact:
        return False
    return any("\u4e00" <= char <= "\u9fff" or char.isalpha() for char in compact)


def _summary_from_text(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if any(keyword in stripped for keyword in ("项目", "Agent", "RAG", "实习", "工作内容")):
            return stripped[:140]
    return "已提取简历文本层，等待人工复核关键项目与岗位匹配度。"


def _merge_model_profile(profile: dict, model_profile: dict) -> dict:
    merged = {**profile}
    for key, value in model_profile.items():
        if value in (None, "", [], {}):
            continue
        if key == "skills":
            merged["skills"] = _merge_skills(profile.get("skills", []), value)
        elif not merged.get(key):
            merged[key] = value
        elif key in {"summary", "education", "projects"}:
            merged[key] = value
    return merged


def _merge_skills(existing: list[str], model_skills: list | str) -> list[str]:
    values = list(existing)
    incoming = model_skills if isinstance(model_skills, list) else [model_skills]
    for item in incoming:
        if isinstance(item, str) and item and item not in values:
            values.append(item)
    return values
