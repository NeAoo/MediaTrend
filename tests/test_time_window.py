from datetime import datetime

from crawlers.base import resolve_query_lookback_hours, resolve_time_window


def test_day_window_uses_rolling_24_hours():
    now = datetime(2026, 5, 20, 16, 30)

    window_start, window_end = resolve_time_window(now, min_hours=0, max_hours=24)

    assert window_start == datetime(2026, 5, 19, 16, 30)
    assert window_end == now


def test_two_day_window_uses_rolling_48_hours():
    now = datetime(2026, 5, 20, 16, 30)

    window_start, window_end = resolve_time_window(now, min_hours=0, max_hours=48)

    assert window_start == datetime(2026, 5, 18, 16, 30)
    assert window_end == now


def test_non_day_hour_window_keeps_rolling_hour_semantics():
    now = datetime(2026, 5, 20, 16, 30)

    window_start, window_end = resolve_time_window(now, min_hours=0, max_hours=12)

    assert window_start == datetime(2026, 5, 20, 4, 30)
    assert window_end == now


def test_query_lookback_uses_configured_max_hours():
    now = datetime(2026, 5, 20, 16, 30)

    assert resolve_query_lookback_hours(now, min_hours=0, max_hours=24) == 24
