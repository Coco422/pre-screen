from services.scoring.app.domain.summary import build_score_summary


def test_final_summary_shape_matches_admin_result_page_expectations():
    summary = build_score_summary(
        objective_score=20,
        subjective_score=30,
        coding_score=40,
        risk_summary={"copy": 1, "visibility_hidden": 2},
    )

    assert summary == {
        "objective_score": 20,
        "subjective_score": 30,
        "coding_score": 40,
        "total_score": 90,
        "risk_summary": {"copy": 1, "visibility_hidden": 2},
    }
