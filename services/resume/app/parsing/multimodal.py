from __future__ import annotations

import base64
from pathlib import Path

from services.resume.app.parsing.model_response import ResumeModelResponse, parse_resume_model_response


def parse_resume_with_model(
    *,
    ai_client,
    page_texts: list[dict],
    page_images: list[Path],
) -> ResumeModelResponse:
    prompt = _build_prompt(page_texts)
    data_urls = [_image_data_url(path) for path in page_images]
    content = ai_client.multimodal_completion(prompt=prompt, image_data_urls=data_urls)
    return parse_resume_model_response(content)


def _build_prompt(page_texts: list[dict]) -> str:
    page_context = "\n\n".join(
        f"第 {page['page_number']} 页文本层：\n{page.get('text', '').strip()}" for page in page_texts
    )
    return (
        "你是招聘简历解析助手。请逐页读取随消息附带的简历页面图片，并结合下面的 PDF 文本层。"
        "输出严格 JSON，不要输出 Markdown fence 之外的说明。JSON 字段："
        "`markdown` 为保留页序的中文 Markdown，必须包含每页 `## 第 N 页：...`；"
        "`profile` 为对象，包含 name、phone、email、role、city、education、skills、projects、summary；"
        "`warnings` 为数组，记录不确定、疑似水印、头像缺失、夸大指标等；"
        "`page_summaries` 为数组，元素包含 page_number、title、summary。"
        "正文不要保留重复水印、哈希串或斜向背景噪声。\n\n"
        f"{page_context}"
    )


def _image_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
