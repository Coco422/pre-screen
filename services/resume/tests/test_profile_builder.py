from services.resume.app.parsing.profile_builder import build_candidate_profile


def test_build_candidate_profile_merges_text_and_model_output():
    profile = build_candidate_profile(
        extracted_pages=[
            {
                "page_number": 1,
                "text": "姓名: 张三\n邮箱: zs@example.com\n技能: Python, Vue, JavaScript",
            },
            {"page_number": 2, "text": "项目经历: 做过后台管理系统"},
        ],
        multimodal_pages=[
            {"page_number": 1, "summary": "候选人头像清晰，页面标题为简历"},
        ],
    )

    assert profile["name"] == "张三"
    assert profile["email"] == "zs@example.com"
    assert "Python" in profile["skills"]
    assert "Vue" in profile["skills"]
    assert "JavaScript" in profile["skills"]
    assert profile["source_summary"]["multimodal_pages"] == [1]
    assert profile["source_summary"]["multimodal_summaries"][1] == "候选人头像清晰，页面标题为简历"
