def _normalize_output(value: str | None) -> str:
    return (value or "").strip()


def build_submission_summary(case_results: list[dict]) -> dict:
    passed_count = sum(1 for item in case_results if item["passed"])
    total_score = sum(item["score"] for item in case_results if item["passed"])
    max_score = sum(item["score"] for item in case_results)
    return {
        "passed_count": passed_count,
        "failed_count": len(case_results) - passed_count,
        "total_score": total_score,
        "max_score": max_score,
    }


def score_case_result(result: dict, testcase: dict) -> dict:
    actual_stdout = result.get("stdout", "")
    expected_stdout = testcase.get("expected_stdout", "")
    passed = _normalize_output(actual_stdout) == _normalize_output(expected_stdout)
    return {
        "stdin": testcase.get("stdin", ""),
        "expected_stdout": expected_stdout,
        "actual_stdout": actual_stdout,
        "score": testcase.get("score", 0),
        "passed": passed,
        "status": result.get("status"),
    }
