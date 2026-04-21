from pre_screen_common.judge0_client import Judge0Client
from services.judge_bridge.app.domain.submission_profiles import build_submission_payload


def execute_sync_case(
    client: Judge0Client,
    *,
    language: str,
    language_id: int,
    source_code: str,
    stdin: str = "",
) -> dict:
    return client.run_sync(
        build_submission_payload(
            language=language,
            language_id=language_id,
            source_code=source_code,
            stdin=stdin,
        )
    )
