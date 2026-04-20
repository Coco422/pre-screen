import struct
import zlib
from pathlib import Path

import fitz

from services.resume.app.tasks.parse_resume import parse_resume_file


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _build_resume_pdf(pdf_path: Path) -> None:
    png_bytes = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")),
            _png_chunk(b"IEND", b""),
        ]
    )

    with fitz.open() as doc:
        page = doc.new_page()
        long_text = "Name: Li Si\n邮箱: li.si@example.com\n技能: Python Vue JavaScript\n" + (
            "负责招聘系统与后台平台建设。" * 80
        )
        page.insert_textbox(fitz.Rect(72, 72, 540, 760), long_text, fontsize=12)

        page = doc.new_page()
        page.insert_text((72, 72), "附加说明")
        page.insert_image(fitz.Rect(72, 120, 120, 168), stream=png_bytes)
        page.insert_image(fitz.Rect(132, 120, 180, 168), stream=png_bytes)

        doc.save(pdf_path)


def test_parse_resume_file_builds_profile_and_marks_multimodal_pages(tmp_path: Path):
    pdf_path = tmp_path / "resume.pdf"
    render_dir = tmp_path / "renders"
    _build_resume_pdf(pdf_path)

    profile = parse_resume_file(pdf_path, render_dir=render_dir)

    assert profile["name"] == "Li Si"
    assert profile["email"] == "li.si@example.com"
    assert "Python" in profile["skills"]
    assert "Vue" in profile["skills"]
    assert profile["source_summary"]["multimodal_pages"] == [2]
    assert (render_dir / "page-2.png").exists()
    assert len(profile["page_metrics"]) == 2
    assert profile["page_metrics"][0]["needs_multimodal"] is False
    assert profile["page_metrics"][1]["needs_multimodal"] is True
