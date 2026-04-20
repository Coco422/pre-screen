from services.scoring.app.domain.objective import score_objective_answer


def test_score_objective_answer_requires_exact_match_for_multi_select():
    score = score_objective_answer(
        answer=["A", "B"],
        answer_key=["A", "B"],
        full_score=5,
        mode="multi_select_exact",
    )

    assert score == 5
