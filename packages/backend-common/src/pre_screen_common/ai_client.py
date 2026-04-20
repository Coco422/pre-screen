from openai import OpenAI


class AIClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url.endswith("/v1"):
            normalized_base_url = f"{normalized_base_url}/v1"

        self._client = OpenAI(api_key=api_key, base_url=normalized_base_url)
        self._model = model

    def simple_text_completion(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
