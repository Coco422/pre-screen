from datetime import datetime, timedelta


def compute_exam_window(start_at: datetime, duration_minutes: int) -> datetime:
    return start_at + timedelta(minutes=duration_minutes)
