from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_COMMON_SRC = REPO_ROOT / "packages" / "backend-common" / "src"
if str(BACKEND_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_COMMON_SRC))

from pre_screen_common.judge0_client import Judge0Client  # noqa: E402


def main() -> None:
    client = Judge0Client(base_url="http://localhost:2358")
    result = client.run_sync(
        {
            "language_id": 71,
            "source_code": "print('hello from judge0')",
        }
    )
    stdout = result.get("stdout")
    if stdout is None:
        raise RuntimeError(f"Judge0 did not return stdout: {result}")
    print(stdout.strip())


if __name__ == "__main__":
    main()
