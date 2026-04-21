def score_objective_answer(
    answer: list[str] | str,
    answer_key: list[str] | str,
    full_score: int,
    mode: str,
) -> int:
    if mode == "multi_select_exact":
        if not isinstance(answer, list) or not isinstance(answer_key, list):
            return 0
        return full_score if sorted(answer) == sorted(answer_key) else 0

    if mode == "single_select":
        return full_score if answer == answer_key else 0

    if mode == "boolean":
        return full_score if str(answer).lower() == str(answer_key).lower() else 0

    return 0
