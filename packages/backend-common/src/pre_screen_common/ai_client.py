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
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    def multimodal_completion(self, *, prompt: str, image_data_urls: list[str]) -> str:
        content: list[dict] = [{"type": "text", "text": prompt}]
        content.extend(
            {"type": "image_url", "image_url": {"url": image_data_url}}
            for image_data_url in image_data_urls
        )
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": content}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""
