from pathlib import Path
import re

import fitz

from services.resume.app.parsing.page_metrics import collect_page_metrics
from services.resume.app.parsing.profile_builder import build_candidate_profile
from services.resume.app.parsing.render_pages import render_pdf_pages

NAME_PATTERN = re.compile(r"(?:姓名|Name)\s*[:：]\s*([^\n\r]+)")


def parse_resume_file(pdf_path: Path, render_dir: Path | None = None) -> dict:
    metrics = collect_page_metrics(pdf_path)

    with fitz.open(str(pdf_path)) as doc:
        extracted_pages = [
            {
                "page_number": page_number,
                "text": doc[page_number - 1].get_text("text") or "",
            }
            for page_number in range(1, doc.page_count + 1)
        ]

    multimodal_page_numbers = [item.page_number for item in metrics if item.needs_multimodal]
    rendered_by_page: dict[int, str] = {}
    if render_dir and multimodal_page_numbers:
        rendered_paths = render_pdf_pages(pdf_path, render_dir, multimodal_page_numbers)
        rendered_by_page = {
            int(path.stem.split("-")[-1]): str(path)
            for path in rendered_paths
        }

    multimodal_pages = [
        {
            "page_number": item.page_number,
            "summary": "queued",
            "image_path": rendered_by_page.get(item.page_number),
        }
        for item in metrics
        if item.needs_multimodal
    ]

    profile = build_candidate_profile(extracted_pages, multimodal_pages)
    name_match = NAME_PATTERN.search(profile["raw_text"])
    profile["name"] = name_match.group(1).strip() if name_match else None
    profile["page_metrics"] = [
        {
            "page_number": item.page_number,
            "text_chars": item.text_chars,
            "image_count": item.image_count,
            "needs_multimodal": item.needs_multimodal,
        }
        for item in metrics
    ]
    return profile
