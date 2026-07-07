import base64
import json
import re
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit, urlunsplit

from openai import OpenAI


class AIClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key, base_url=self._normalize_base_url(base_url))
        self._model = model

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        parsed_url = urlsplit(base_url.rstrip("/"))
        if parsed_url.path in {"", "/"}:
            parsed_url = parsed_url._replace(path="/v1")
        return urlunsplit(parsed_url)

    def simple_text_completion(self, prompt: str) -> str:
        return self.complete(user_prompt=prompt, temperature=0.1)

    def complete(
        self,
        *,
        user_prompt: str,
        system_prompt: str | None = None,
        images: Sequence[Path] | None = None,
        temperature: float = 0.1,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if images:
            content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
            for image_path in images:
                data_url = self._image_to_data_url(image_path)
                content.append({"type": "image_url", "image_url": {"url": data_url}})
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def json_completion(
        self,
        *,
        user_prompt: str,
        system_prompt: str | None = None,
        images: Sequence[Path] | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        raw_content = self.complete(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            images=images,
            temperature=temperature,
        )
        return self._coerce_json_object(raw_content)

    @staticmethod
    def _image_to_data_url(image_path: Path) -> str:
        suffix = image_path.suffix.lower().lstrip(".") or "png"
        mime_type = "image/png" if suffix == "png" else f"image/{suffix}"
        encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _coerce_json_object(raw_content: str) -> dict[str, Any]:
        cleaned = raw_content.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()

        if not cleaned.startswith("{"):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end >= start:
                cleaned = cleaned[start : end + 1]

        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Model did not return a JSON object.")
        return parsed
