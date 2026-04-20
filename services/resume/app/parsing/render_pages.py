from pathlib import Path
from typing import Sequence

import fitz


def render_pdf_pages(
    pdf_path: Path,
    output_dir: Path,
    page_numbers: Sequence[int] | None = None,
    zoom: float = 2.0,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_pages = set(page_numbers or [])
    rendered_paths: list[Path] = []

    with fitz.open(str(pdf_path)) as doc:
        for page_number, page in enumerate(doc, start=1):
            if selected_pages and page_number not in selected_pages:
                continue
            pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            image_path = output_dir / f"page-{page_number}.png"
            pixmap.save(image_path)
            rendered_paths.append(image_path)

    return rendered_paths
