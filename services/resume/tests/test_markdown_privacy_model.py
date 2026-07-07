import pytest

from services.resume.app.parsing.markdown import build_resume_markdown, clean_resume_text
from services.resume.app.parsing.model_response import parse_resume_model_response
from services.resume.app.parsing.privacy import mask_email, mask_phone


def test_clean_resume_text_removes_watermark_tokens_and_keeps_content():
    text = "姓名：丁柯\n3a223f11db7d0d0d1HFz3N69EldWx426UfOYWOWgnvDRNxhm2A~~\n技能：Python"

    cleaned, warnings = clean_resume_text(text)

    assert "WOW" not in cleaned
    assert "姓名：丁柯" in cleaned
    assert "技能：Python" in cleaned
    assert warnings


def test_build_resume_markdown_preserves_page_boundaries():
    markdown, warnings = build_resume_markdown(
        title="测试简历",
        pages=[
            {"page_number": 1, "text": "姓名：张三\n个人信息\n电话：18800000000"},
            {"page_number": 2, "text": "项目经历\n负责后台系统"},
        ],
    )

    assert "# 测试简历" in markdown
    assert "## 第 1 页" in markdown
    assert "## 第 2 页" in markdown
    assert "### 项目经历" in markdown
    assert warnings == []


def test_mask_phone_and_email():
    assert mask_phone("18863226774") == "188****6774"
    assert mask_email("2413951813@qq.com") == "24***3@qq.com"


def test_parse_resume_model_response_accepts_fenced_json():
    response = parse_resume_model_response(
        '```json\n{"markdown":"## 第 1 页：简历","profile":{"name":"张三"},"warnings":[]}\n```'
    )

    assert response.markdown == "## 第 1 页：简历"
    assert response.profile["name"] == "张三"


def test_parse_resume_model_response_rejects_invalid_payload():
    with pytest.raises(ValueError):
        parse_resume_model_response("not json")
