from pre_screen_common.judge0_client import Judge0Client


def execute_sync_case(
    client: Judge0Client,
    *,
    language_id: int,
    source_code: str,
    stdin: str = "",
) -> dict:
    return client.run_sync(
        {
            "language_id": language_id,
            "source_code": source_code,
            "stdin": stdin,
        }
    )
