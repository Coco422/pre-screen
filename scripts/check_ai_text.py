from pathlib import Path
import os
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_COMMON_SRC = REPO_ROOT / "packages" / "backend-common" / "src"
if str(BACKEND_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_COMMON_SRC))

from pre_screen_common.ai_client import AIClient  # noqa: E402


def main() -> None:
    client = AIClient(
        api_key=os.environ["AI_API_KEY"],
        base_url=os.environ["AI_BASE_URL"],
        model=os.environ["AI_MODEL"],
    )
    print(client.simple_text_completion("请只回复 pong"))


if __name__ == "__main__":
    main()
