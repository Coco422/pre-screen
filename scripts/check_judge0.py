import os
from pathlib import Path
import platform
import sys
from urllib.parse import urlparse

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
BACKEND_COMMON_SRC = REPO_ROOT / "packages" / "backend-common" / "src"
if str(BACKEND_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_COMMON_SRC))

from pre_screen_common.judge0_client import Judge0Client  # noqa: E402
from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS  # noqa: E402
from services.judge_bridge.app.domain.submission_profiles import build_submission_payload  # noqa: E402


SMOKE_CASES = {
    "c": '#include <stdio.h>\nint main(){puts("hello from judge0 c");return 0;}',
    "cpp": '#include <iostream>\nint main(){std::cout<<"hello from judge0 cpp\\n";return 0;}',
    "java": 'class Main { public static void main(String[] args){ System.out.println("hello from judge0 java"); } }',
    "javascript": 'console.log("hello from judge0 javascript")',
    "python": "print('hello from judge0 python')",
}


def run_case(client: Judge0Client, language: str, source_code: str) -> None:
    try:
        result = client.run_sync(
            build_submission_payload(
                language=language,
                language_id=PRODUCT_LANGUAGE_IDS[language],
                source_code=source_code,
            )
        )
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip() or "empty response body"
        raise RuntimeError(f"Judge0 returned {exc.response.status_code} for {exc.request.url}: {body}") from exc

    stdout = result.get("stdout")
    if stdout is None:
        status = result.get("status") or {}
        detail = result.get("message") or status.get("description") or "no stdout returned"
        raise RuntimeError(f"Judge0 execution failed for {language} ({detail}): {result}")
    print(f"{language}: {stdout.strip()}")


def main() -> None:
    base_url = os.environ.get("JUDGE0_BASE_URL", "http://192.168.100.189:2360")
    client = Judge0Client(base_url=base_url)
    host = (urlparse(base_url).hostname or "").lower()
    if platform.system() == "Darwin" and platform.machine() == "arm64" and host in {
        "",
        "localhost",
        "127.0.0.1",
        "judge0",
    }:
        print("skip: local Judge0 execution is unreliable on macOS arm64; verify on Linux amd64 or a remote Judge0 host")
        return

    smoke_cases = dict(SMOKE_CASES)
    for language, source_code in smoke_cases.items():
        run_case(client, language, source_code)


if __name__ == "__main__":
    main()
