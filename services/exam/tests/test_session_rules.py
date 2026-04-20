from datetime import datetime, timedelta, timezone

from services.exam.app.domain.session_rules import compute_exam_window


def test_compute_exam_window_sets_server_side_expiration():
    start_at = datetime(2026, 4, 21, 10, 0, tzinfo=timezone.utc)
    expire_at = compute_exam_window(start_at, duration_minutes=90)

    assert expire_at == start_at + timedelta(minutes=90)
