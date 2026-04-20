import os
from pathlib import Path
import sys

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_COMMON_SRC = REPO_ROOT / "packages" / "backend-common" / "src"
if str(BACKEND_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_COMMON_SRC))

from pre_screen_common.judge0_client import Judge0Client  # noqa: E402


def main() -> None:
    client = Judge0Client(base_url=os.environ.get("JUDGE0_BASE_URL", "http://localhost:2358"))
    try:
        result = client.run_sync(
            {
                "language_id": 71,
                "source_code": "print('hello from judge0')",
            }
        )
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip() or "empty response body"
        raise RuntimeError(f"Judge0 returned {exc.response.status_code} for {exc.request.url}: {body}") from exc

    stdout = result.get("stdout")
    if stdout is None:
        status = result.get("status") or {}
        detail = result.get("message") or status.get("description") or "no stdout returned"
        raise RuntimeError(f"Judge0 execution failed ({detail}): {result}")
    print(stdout.strip())


if __name__ == "__main__":
    main()
