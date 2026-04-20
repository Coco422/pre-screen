from services.exam.app.domain.paper_generator import generate_paper_draft


def test_generate_paper_draft_keeps_fixed_question_mix():
    paper = generate_paper_draft(
        job_template={
            "name": "frontend-intern",
            "objective_count": 4,
            "subjective_count": 2,
            "coding_count": 1,
        },
        jd_text="前端工程师，需要熟悉 Vue、TypeScript、工程化。",
        candidate_profile={"skills": ["Vue", "TypeScript"], "projects": ["后台管理系统"]},
    )

    assert paper["template_name"] == "frontend-intern"
    assert paper["question_mix"] == {"base_info": 1, "objective": 4, "subjective": 2, "coding": 1}
    assert len(paper["questions"]) == 8
    assert paper["questions"][0]["type"] == "base_info"
    assert paper["questions"][-1]["type"] == "coding"
    assert "Vue" in paper["candidate_signals"]
    assert paper["prompt_version"] == "paper-draft/v1"


def test_generate_paper_draft_reports_actual_question_mix():
    paper = generate_paper_draft(
        job_template={
            "name": "frontend-intern",
            "base_info_count": 2,
            "objective_count": 8,
            "subjective_count": 5,
            "coding_count": 3,
        },
        jd_text="前端工程师，需要熟悉 Vue、TypeScript、工程化。",
        candidate_profile={"skills": ["Vue", "TypeScript"], "projects": ["后台管理系统"]},
    )

    actual_mix: dict[str, int] = {}
    for question in paper["questions"]:
        actual_mix[question["type"]] = actual_mix.get(question["type"], 0) + 1

    assert paper["question_mix"] == actual_mix
