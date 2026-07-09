from pre_screen_common.status import (
    CANDIDATE_EXTRACTING,
    CANDIDATE_READY_TO_PUBLISH,
    candidate_status_label,
    is_ready_to_publish,
    is_screening_in_progress,
    normalize_candidate_status,
)


def test_normalize_legacy_labels_to_codes():
    assert normalize_candidate_status("解析中") == CANDIDATE_EXTRACTING
    assert normalize_candidate_status("待发卷") == CANDIDATE_READY_TO_PUBLISH
    assert normalize_candidate_status(CANDIDATE_EXTRACTING) == CANDIDATE_EXTRACTING


def test_labels_and_dashboard_helpers():
    assert candidate_status_label("解析中") == "信息提取中"
    assert is_screening_in_progress("待审核")
    assert is_ready_to_publish("待发卷")
