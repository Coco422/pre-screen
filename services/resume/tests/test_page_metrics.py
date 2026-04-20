import struct
import zlib
from pathlib import Path

import fitz

from services.resume.app.parsing.page_metrics import collect_page_metrics


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _build_sample_pdf(pdf_path: Path) -> None:
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
        long_text = "Alpha beta gamma delta epsilon " * 100
        page.insert_textbox(fitz.Rect(72, 72, 540, 760), long_text, fontsize=12)

        page = doc.new_page()
        page.insert_text((72, 72), "Short page")

        page = doc.new_page()
        page.insert_text((72, 72), "Some supporting text")
        page.insert_image(fitz.Rect(72, 120, 120, 168), stream=png_bytes)
        page.insert_image(fitz.Rect(132, 120, 180, 168), stream=png_bytes)

        doc.save(pdf_path)


def test_collect_page_metrics_uses_sample_pdf(tmp_path: Path):
    sample = tmp_path / "sample.pdf"
    _build_sample_pdf(sample)

    metrics = collect_page_metrics(sample)

    assert [item.page_number for item in metrics] == [1, 2, 3]
    assert metrics[0].text_chars > 1000
    assert metrics[0].image_count == 0
    assert metrics[0].needs_multimodal is False
    assert metrics[1].text_chars < 100
    assert metrics[1].image_count == 0
    assert metrics[1].needs_multimodal is True
    assert metrics[2].image_count == 2
    assert metrics[2].needs_multimodal is True
