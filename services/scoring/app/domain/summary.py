def build_score_summary(
    objective_score: int,
    subjective_score: int,
    coding_score: int,
    risk_summary: dict,
) -> dict:
    total_score = objective_score + subjective_score + coding_score
    return {
        "objective_score": objective_score,
        "subjective_score": subjective_score,
        "coding_score": coding_score,
        "total_score": total_score,
        "risk_summary": risk_summary,
        "has_risk_flags": bool(risk_summary),
    }
