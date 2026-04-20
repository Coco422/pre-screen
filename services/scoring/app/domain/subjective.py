def suggest_subjective_score(answer_text: str, rubric_text: str, max_score: int) -> dict:
    cleaned_answer = answer_text.strip()
    if not cleaned_answer:
        return {
            "suggested_score": 0,
            "reasoning_summary": "回答为空，建议人工重点复核。",
        }

    keyword_hits = sum(
        1
        for keyword in ("项目", "技术", "问题", "优化", "性能", "复盘", "系统")
        if keyword in cleaned_answer or keyword in rubric_text
    )
    length_ratio = min(len(cleaned_answer) / 80, 1.0)
    score_ratio = min(1.0, 0.35 + length_ratio * 0.45 + keyword_hits * 0.04)
    suggested_score = min(max_score, max(1, round(max_score * score_ratio)))

    return {
        "suggested_score": suggested_score,
        "reasoning_summary": f"回答长度较为充分，命中 {keyword_hits} 个评分关注点，建议人工确认。",
    }
