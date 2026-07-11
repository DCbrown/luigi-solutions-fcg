"""The weekly window is pure arithmetic — pin it (docs/decisions.md D10).

The Supabase count/insert halves of quota.py talk to a live service and are
deliberately untested here; what must never drift is where a week starts.
"""

from datetime import datetime, timedelta, timezone

from quota import WEEKLY_LIMIT, next_week_start, week_start

UTC = timezone.utc


def test_the_limit_is_three():
    assert WEEKLY_LIMIT == 3


def test_midweek_snaps_back_to_monday_midnight():
    wednesday = datetime(2026, 7, 8, 15, 30, 12, tzinfo=UTC)
    assert week_start(wednesday) == datetime(2026, 7, 6, tzinfo=UTC)


def test_monday_midnight_is_its_own_week_start():
    monday = datetime(2026, 7, 6, 0, 0, 0, tzinfo=UTC)
    assert week_start(monday) == monday


def test_sunday_night_still_belongs_to_the_old_week():
    sunday_night = datetime(2026, 7, 12, 23, 59, 59, tzinfo=UTC)
    assert week_start(sunday_night) == datetime(2026, 7, 6, tzinfo=UTC)


def test_reset_is_the_following_monday():
    wednesday = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
    assert next_week_start(wednesday) == datetime(2026, 7, 13, tzinfo=UTC)


def test_every_weekday_maps_into_one_seven_day_window():
    start = datetime(2026, 7, 6, tzinfo=UTC)
    for offset_hours in range(0, 7 * 24, 7):
        moment = start + timedelta(hours=offset_hours)
        assert week_start(moment) == start
        assert start <= moment < next_week_start(moment)
