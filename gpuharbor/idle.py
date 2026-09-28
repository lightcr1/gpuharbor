from __future__ import annotations


def should_stop_for_idle(idle_seconds: float, idle_minutes: int) -> bool:
    """Pure policy used by the background loop and unit tests."""
    return idle_minutes > 0 and idle_seconds >= idle_minutes * 60
