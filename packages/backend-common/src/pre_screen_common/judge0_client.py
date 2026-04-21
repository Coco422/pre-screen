import httpx


class Judge0Client:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def list_languages(self) -> list[dict]:
        response = httpx.get(f"{self._base_url}/languages", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def run_sync(self, payload: dict) -> dict:
        response = httpx.post(f"{self._base_url}/submissions?wait=true", json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()
