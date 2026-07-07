import struct
import zlib
from pathlib import Path

import fitz

from services.resume.app.parsing.avatar import extract_avatar


def _png_bytes(width: int, height: int, rgb: bytes = b"\x7f\x7f\x7f") -> bytes:
    raw_rows = b"".join(b"\x00" + rgb * width for _ in range(height))
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw_rows)),
            _png_chunk(b"IEND", b""),
        ]
    )


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def test_extract_avatar_finds_top_page_portrait_and_rejects_icons(tmp_path: Path):
    pdf_path = tmp_path / "avatar.pdf"
    output_dir = tmp_path / "assets"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "姓名：测试候选人\n电话：18800000000")
        page.insert_image(fitz.Rect(36, 36, 58, 58), stream=_png_bytes(32, 32))
        page.insert_image(fitz.Rect(488, 36, 548, 120), stream=_png_bytes(160, 224))
        doc.save(pdf_path)

    avatar = extract_avatar(pdf_path, output_dir)

    assert avatar.status == "found"
    assert avatar.page_number == 1
    assert avatar.bbox == (488.0, 36.0, 548.0, 120.0)
    assert avatar.image_path
    assert Path(avatar.image_path).exists()


def test_extract_avatar_reports_not_found_for_text_only_pdf(tmp_path: Path):
    pdf_path = tmp_path / "plain.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "王锦润\n18863226774\n2413951813@qq.com")
        doc.save(pdf_path)

    avatar = extract_avatar(pdf_path, tmp_path / "assets")

    assert avatar.status == "not_found"
    assert avatar.reason == "no portrait-like top-page image found"
