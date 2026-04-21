from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True, slots=True)
class PageMetric:
    page_number: int
    text_chars: int
    image_count: int
    needs_multimodal: bool


def collect_page_metrics(pdf_path: Path) -> list[PageMetric]:
    metrics: list[PageMetric] = []

    with fitz.open(str(pdf_path)) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            text_chars = len(text.strip())
            image_count = len(page.get_images(full=True))
            needs_multimodal = text_chars < 600 or (text_chars < 1200 and image_count > 1)
            metrics.append(
                PageMetric(
                    page_number=page_number,
                    text_chars=text_chars,
                    image_count=image_count,
                    needs_multimodal=needs_multimodal,
                )
            )

    return metrics
