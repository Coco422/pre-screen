from collections import Counter


OBJECTIVE_BANK = [
    {
        "question_id": "obj-vue-reactivity",
        "type": "objective",
        "title": "Vue 响应式原理基础",
        "score": 5,
        "tags": ("Vue", "frontend"),
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
        "tags": ("工程化", "frontend"),
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
]

SUBJECTIVE_BANK = [
    {
        "question_id": "sub-project-review",
        "type": "subjective",
        "title": "请复盘一个你最熟悉的项目",
        "score": 15,
        "tags": ("项目", "复盘"),
    },
    {
        "question_id": "sub-debug-story",
        "type": "subjective",
        "title": "描述一个你定位问题的过程",
        "score": 15,
        "tags": ("定位问题", "排障"),
    },
    {
        "question_id": "sub-tech-tradeoff",
        "type": "subjective",
        "title": "说说你在技术选型中的一次取舍",
        "score": 15,
        "tags": ("技术取舍",),
    },
]

CODING_BANK = [
    {
        "question_id": "code-array-dedupe-js",
        "type": "coding",
        "title": "实现一个数组去重函数",
        "score": 50,
        "language": "javascript",
        "tags": ("JavaScript", "TypeScript", "frontend"),
    },
    {
        "question_id": "code-two-sum-python",
        "type": "coding",
        "title": "实现 Two Sum",
        "score": 50,
        "language": "python",
        "tags": ("Python", "backend"),
    },
]


def _score_question(item: dict, signals: set[str], jd_text: str) -> tuple[int, int]:
    jd_lower = jd_text.lower()
    score = 0
    for tag in item.get("tags", ()):
        tag_lower = str(tag).lower()
        if tag in signals:
            score += 3
        if tag_lower in jd_lower:
            score += 2
    return score, -len(item["question_id"])


def _pick_questions(bank: list[dict], count: int, signals: set[str], jd_text: str) -> list[dict]:
    ranked = sorted(
        bank,
        key=lambda item: (_score_question(item, signals, jd_text), item["question_id"]),
        reverse=True,
    )
    return ranked[:count]


def _build_base_info_questions(count: int) -> list[dict]:
    base_fields = ["姓名", "手机号", "邮箱", "城市", "身高", "体重", "爱好"]
    questions: list[dict] = []
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


def generate_paper_draft(job_template: dict, jd_text: str, candidate_profile: dict) -> dict:
    objective_count = job_template["objective_count"]
    subjective_count = job_template["subjective_count"]
    coding_count = job_template["coding_count"]
    base_info_count = job_template.get("base_info_count", 1)

    candidate_skills = candidate_profile.get("skills", [])
    template_tags = job_template.get("tags", [])
    signals = {str(item) for item in [*candidate_skills, *template_tags]}

    questions = _build_base_info_questions(base_info_count)
    questions.extend(_pick_questions(OBJECTIVE_BANK, objective_count, signals, jd_text))
    questions.extend(_pick_questions(SUBJECTIVE_BANK, subjective_count, signals, jd_text))
    questions.extend(_pick_questions(CODING_BANK, coding_count, signals, jd_text))

    question_mix = Counter(question["type"] for question in questions)
    return {
        "template_name": job_template["name"],
        "question_mix": dict(question_mix),
        "questions": questions,
        "prompt_version": "paper-draft/v1",
        "jd_summary": jd_text[:120],
        "candidate_signals": candidate_skills,
        "question_type_counts": dict(question_mix),
    }
