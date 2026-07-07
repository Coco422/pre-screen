import struct
import zlib
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from services.resume.app.domain.models import ResumeUpload
from services.resume.app.main import app
from services.resume.app.repositories.resume_repository import resume_repository


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _png_bytes(width: int, height: int) -> bytes:
    raw_rows = b"".join(b"\x00" + b"\x99\x99\x99" * width for _ in range(height))
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw_rows)),
            _png_chunk(b"IEND", b""),
        ]
    )


def test_resume_pipeline_parse_markdown_and_avatar_routes(tmp_path: Path):
    resume_repository.reset()
    pdf_path = tmp_path / "resume.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "姓名：赵六\n电话：18800000000\n邮箱：zhao@example.com\n技能：Python")
        page.insert_image(fitz.Rect(488, 36, 548, 120), stream=_png_bytes(160, 224))
        doc.save(pdf_path)
    resume_repository.save_upload(
        ResumeUpload(
            upload_id="file-api",
            candidate_name="赵六",
            original_filename="resume.pdf",
            object_key="resumes/file-api.pdf",
            content_type="application/pdf",
            size_bytes=pdf_path.stat().st_size,
            local_path=str(pdf_path),
        )
    )
    client = TestClient(app)

    parse_response = client.post("/internal/resumes/file-api/parse", json={"use_ai": False})
    markdown_response = client.get("/internal/resumes/file-api/markdown")
    avatar_response = client.get("/internal/resumes/file-api/assets/avatar")

    assert parse_response.status_code == 200
    assert parse_response.json()["profile"]["name"] == "赵六"
    assert markdown_response.status_code == 200
    assert "## 第 1 页" in markdown_response.json()["markdown"]
    assert avatar_response.status_code == 200
    assert avatar_response.json()["status"] == "found"
    assert avatar_response.json()["asset_url"] == "/internal/resumes/file-api/assets/avatar/file"
    resume_repository.reset()
