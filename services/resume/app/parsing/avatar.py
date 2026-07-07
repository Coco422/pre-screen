from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from services.resume.app.domain.models import AvatarAsset


@dataclass(frozen=True, slots=True)
class ImageObject:
    page_number: int
    xref: int
    width: int
    height: int
    bbox: tuple[float, float, float, float]
    score: float


def collect_image_objects(pdf_path: Path) -> list[dict]:
    objects: list[dict] = []
    with fitz.open(str(pdf_path)) as doc:
        for page_number, page in enumerate(doc, start=1):
            seen_xrefs: set[int] = set()
            for image in page.get_images(full=True):
                xref = image[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                extracted = doc.extract_image(xref)
                rects = page.get_image_rects(xref)
                objects.append(
                    {
                        "page_number": page_number,
                        "xref": xref,
                        "width": extracted.get("width"),
                        "height": extracted.get("height"),
                        "ext": extracted.get("ext"),
                        "bboxes": [_rect_tuple(rect) for rect in rects],
                    }
                )
    return objects


def extract_avatar(pdf_path: Path, output_dir: Path | None = None) -> AvatarAsset:
    with fitz.open(str(pdf_path)) as doc:
        candidate = _best_avatar_candidate(doc)
        if candidate is None:
            return AvatarAsset(status="not_found", reason="no portrait-like top-page image found")

        image_path: str | None = None
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            page = doc[candidate.page_number - 1]
            rect = fitz.Rect(candidate.bbox)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=rect, alpha=False)
            target = output_dir / f"avatar-page-{candidate.page_number}-xref-{candidate.xref}.png"
            pixmap.save(target)
            image_path = str(target)

        return AvatarAsset(
            status="found",
            page_number=candidate.page_number,
            xref=candidate.xref,
            bbox=candidate.bbox,
            image_path=image_path,
            width=candidate.width,
            height=candidate.height,
        )


def _best_avatar_candidate(doc: fitz.Document) -> ImageObject | None:
    candidates: list[ImageObject] = []
    for page_number, page in enumerate(doc, start=1):
        if page_number > 2:
            break
        seen_xrefs: set[int] = set()
        for image in page.get_images(full=True):
            xref = image[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            extracted = doc.extract_image(xref)
            pixel_width = int(extracted.get("width") or 0)
            pixel_height = int(extracted.get("height") or 0)
            for rect in page.get_image_rects(xref):
                score = _avatar_score(page.rect, rect, pixel_width, pixel_height)
                if score > 0:
                    candidates.append(
                        ImageObject(
                            page_number=page_number,
                            xref=xref,
                            width=pixel_width,
                            height=pixel_height,
                            bbox=_rect_tuple(rect),
                            score=score,
                        )
                    )
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.score)


def _avatar_score(page_rect: fitz.Rect, rect: fitz.Rect, pixel_width: int, pixel_height: int) -> float:
    if pixel_width < 100 or pixel_height < 140:
        return 0
    if rect.width < 35 or rect.height < 50:
        return 0
    aspect = rect.height / max(rect.width, 1)
    if aspect < 1.15 or aspect > 1.8:
        return 0
    if rect.y0 > page_rect.height * 0.35:
        return 0
    score = rect.width * rect.height
    if rect.x0 > page_rect.width * 0.7 or rect.x1 < page_rect.width * 0.25:
        score *= 1.3
    if rect.y1 < page_rect.height * 0.22:
        score *= 1.2
    return score


def _rect_tuple(rect: fitz.Rect) -> tuple[float, float, float, float]:
    return (round(rect.x0, 1), round(rect.y0, 1), round(rect.x1, 1), round(rect.y1, 1))
