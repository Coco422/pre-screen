COMMON_SUBMISSION_OVERRIDES = {
    "enable_per_process_and_thread_time_limit": True,
    "enable_per_process_and_thread_memory_limit": True,
}

LANGUAGE_SUBMISSION_OVERRIDES = {
    "java": {
        "memory_limit": 3_145_728,
        "max_processes_and_or_threads": 120,
    },
    "javascript": {
        "memory_limit": 1_048_576,
    },
    "typescript": {
        "memory_limit": 1_048_576,
    },
}


def build_submission_payload(
    *,
    language: str,
    language_id: int,
    source_code: str,
    stdin: str = "",
) -> dict:
    payload = {
        "language_id": language_id,
        "source_code": source_code,
        "stdin": stdin,
    }
    payload.update(COMMON_SUBMISSION_OVERRIDES)
    payload.update(LANGUAGE_SUBMISSION_OVERRIDES.get(language, {}))
    return payload
