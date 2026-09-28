from datetime import datetime
from zoneinfo import ZoneInfo


def is_blocked(value: datetime) -> bool:
    local = value.astimezone(ZoneInfo("Europe/Zurich"))
    return local.weekday() < 5 and 7 <= local.hour < 18


def test_weekday_work_hours_are_blocked():
    assert is_blocked(datetime(2026, 9, 28, 10, tzinfo=ZoneInfo("Europe/Zurich")))


def test_evening_and_weekend_are_allowed():
    assert not is_blocked(datetime(2026, 9, 28, 18, tzinfo=ZoneInfo("Europe/Zurich")))
    assert not is_blocked(datetime(2026, 10, 3, 10, tzinfo=ZoneInfo("Europe/Zurich")))
