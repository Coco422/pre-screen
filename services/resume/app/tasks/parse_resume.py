from pathlib import Path
import os

import fitz

from pre_screen_common.ai_client import AIClient
from services.resume.app.parsing.avatar import collect_image_objects, extract_avatar
from services.resume.app.parsing.markdown import build_resume_markdown
from services.resume.app.parsing.model_response import ResumeModelResponse
from services.resume.app.parsing.multimodal import parse_resume_with_model
from services.resume.app.parsing.page_metrics import collect_page_metrics
from services.resume.app.parsing.profile_builder import build_candidate_profile
from services.resume.app.parsing.render_pages import render_pdf_pages

def parse_resume_file(
    pdf_path: Path,
    render_dir: Path | None = None,
    *,
    ai_client: AIClient | None = None,
    use_ai: bool | None = None,
) -> dict:
    metrics = collect_page_metrics(pdf_path)

    with fitz.open(str(pdf_path)) as doc:
        extracted_pages = [
            {
                "page_number": page_number,
                "text": doc[page_number - 1].get_text("text") or "",
            }
            for page_number in range(1, doc.page_count + 1)
        ]

    should_use_ai = _should_use_ai(use_ai=use_ai, ai_client=ai_client)
    multimodal_page_numbers = [item.page_number for item in metrics if item.needs_multimodal]
    rendered_by_page: dict[int, str] = {}
    model_response: ResumeModelResponse | None = None
    parse_warnings: list[str] = []
    if render_dir and (multimodal_page_numbers or should_use_ai):
        render_page_numbers = (
            [item.page_number for item in metrics] if should_use_ai else multimodal_page_numbers
        )
        rendered_paths = render_pdf_pages(pdf_path, render_dir, render_page_numbers)
        rendered_by_page = {
            int(path.stem.split("-")[-1]): str(path)
            for path in rendered_paths
        }
        if should_use_ai:
            ai_client = ai_client or _default_ai_client()
            if ai_client is None:
                parse_warnings.append("AI_API_KEY is not configured; used deterministic PDF fallback.")
            else:
                try:
                    model_response = parse_resume_with_model(
                        ai_client=ai_client,
                        page_texts=extracted_pages,
                        page_images=rendered_paths,
                    )
                except Exception as exc:  # pragma: no cover - defensive fallback around remote model
                    parse_warnings.append(f"multimodal model failed; used PDF fallback: {exc}")

    multimodal_pages = [
        {
            "page_number": item.page_number,
            "summary": "parsed_by_model" if model_response else "queued",
            "image_path": rendered_by_page.get(item.page_number),
        }
        for item in metrics
        if item.needs_multimodal or should_use_ai
    ]

    profile = build_candidate_profile(
        extracted_pages,
        multimodal_pages,
        model_profile=model_response.profile if model_response else None,
    )
    title = profile.get("name") or pdf_path.stem
    markdown, markdown_warnings = build_resume_markdown(
        title=title,
        pages=extracted_pages,
        model_markdown=model_response.markdown if model_response else None,
    )
    parse_warnings.extend(markdown_warnings)
    avatar_dir = render_dir / "assets" if render_dir else None
    avatar = extract_avatar(pdf_path, avatar_dir)
    avatar_payload = {
        "status": avatar.status,
        "page_number": avatar.page_number,
        "xref": avatar.xref,
        "bbox": avatar.bbox,
        "image_path": avatar.image_path,
        "width": avatar.width,
        "height": avatar.height,
        "reason": avatar.reason,
    }
    if avatar.status != "found":
        parse_warnings.append(f"avatar not found: {avatar.reason}")
    profile["page_metrics"] = [
        {
            "page_number": item.page_number,
            "text_chars": item.text_chars,
            "image_count": item.image_count,
            "needs_multimodal": item.needs_multimodal,
        }
        for item in metrics
    ]
    profile["markdown"] = markdown
    profile["avatar"] = avatar_payload
    profile["metadata"] = {
        "file_name": pdf_path.name,
        "page_count": len(extracted_pages),
        "text_length": len(profile["raw_text"].strip()),
        "image_objects": collect_image_objects(pdf_path),
        "avatar": avatar_payload,
        "warnings": parse_warnings,
        "model_used": model_response is not None,
        "model_page_summaries": model_response.page_summaries if model_response else [],
    }
    return profile


def _should_use_ai(*, use_ai: bool | None, ai_client: AIClient | None) -> bool:
    if use_ai is not None:
        return use_ai
    return ai_client is not None or bool(os.environ.get("AI_API_KEY"))


def _default_ai_client() -> AIClient | None:
    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        return None
    return AIClient(
        api_key=api_key,
        base_url=os.environ.get("AI_BASE_URL", "http://172.16.99.204:3398"),
        model=os.environ.get("AI_MODEL", "qwen3.6-27b"),
    )
