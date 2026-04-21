from services.scoring.app.domain.summary import build_score_summary


def test_build_score_summary_combines_objective_subjective_and_coding_scores():
    summary = build_score_summary(
        objective_score=20,
        subjective_score=25,
        coding_score=40,
        risk_summary={"copy": 1},
    )

    assert summary["total_score"] == 85
