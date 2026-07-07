import struct
import zlib
from pathlib import Path

import fitz

from services.resume.app.repositories.resume_repository import resume_repository
from services.resume.app.tasks.batch_extract import run_resume_batch


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _png_bytes(width: int, height: int) -> bytes:
    raw_rows = b"".join(b"\x00" + b"\xaa\xaa\xaa" * width for _ in range(height))
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw_rows)),
            _png_chunk(b"IEND", b""),
        ]
    )


def _resume_pdf(path: Path, name: str, with_avatar: bool) -> None:
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"姓名：{name}\n电话：18800000000\n邮箱：test@example.com\n项目经历\nAgent RAG Python Vue",
        )
        if with_avatar:
            page.insert_image(fitz.Rect(488, 36, 548, 120), stream=_png_bytes(160, 224))
        doc.save(path)


def test_run_resume_batch_writes_markdown_metadata_avatar_and_analysis(tmp_path: Path):
    resume_repository.reset()
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    _resume_pdf(first, "张三", with_avatar=True)
    _resume_pdf(second, "李四", with_avatar=False)

    result = run_resume_batch(
        pdf_paths=[first, second],
        output_root=tmp_path / "batches",
        batch_id="sample",
        use_ai=False,
    )

    output_dir = Path(result.output_dir)
    assert (output_dir / "common-analysis.md").exists()
    assert "技能矩阵" in result.analysis_markdown
    assert len(result.file_ids) == 2
    assert len(resume_repository.list_parse_results()) == 2
    assert list(output_dir.glob("*/resume.md"))
    assert list(output_dir.glob("*/metadata.json"))
    assert list(output_dir.glob("*/pages/assets/avatar-*.png"))
