from services.scoring.app.domain.subjective import suggest_subjective_score


def suggest_subjective_reviews(items: list[dict]) -> list[dict]:
    suggestions: list[dict] = []
    for item in items:
        suggestion = suggest_subjective_score(
            answer_text=item["answer_text"],
            rubric_text=item["rubric_text"],
            max_score=item["max_score"],
        )
        suggestions.append(
            {
                "question_title": item["question_title"],
                "answer_text": item["answer_text"],
                "max_score": item["max_score"],
                **suggestion,
            }
        )
    return suggestions
