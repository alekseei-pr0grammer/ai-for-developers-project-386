"""Slots: the start times a Guest can pick. Derived, never stored."""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.schedule import Interval


def compute_slots(
    *,
    schedule: list[Interval],
    time_zone: str,
    duration: timedelta,
    now: datetime,
    window_days: int,
    start: datetime,
    end: datetime,
) -> list[datetime]:
    """Slot starts (UTC) in [start, end), not before `now` and within the booking window.

    Within each Weekly Schedule interval, Slots start at the interval's start and step
    by `duration`; a Slot must end by the interval's end. Local hours are converted per
    day in the Host's time zone, so daylight saving changes are respected.
    """
    zone = ZoneInfo(time_zone)
    today = now.astimezone(zone).date()
    window_end = _local_midnight(today + timedelta(days=window_days), zone)
    lower, upper = max(start, now), min(end, window_end)
    return [
        slot
        for day in _days(today, window_days)
        for slot in _day_slots(day, schedule, zone, duration)
        if lower <= slot < upper
    ]


def _days(first: date, count: int) -> Iterator[date]:
    for offset in range(count):
        yield first + timedelta(days=offset)


def _local_midnight(day: date, zone: ZoneInfo) -> datetime:
    return datetime.combine(day, datetime.min.time(), zone)


def _day_slots(
    day: date, schedule: list[Interval], zone: ZoneInfo, duration: timedelta
) -> Iterator[datetime]:
    for weekday, start, end in schedule:
        if weekday != day.weekday():
            continue
        slot = datetime.combine(day, start, zone).astimezone(UTC)
        interval_end = datetime.combine(day, end, zone).astimezone(UTC)
        while slot + duration <= interval_end:
            yield slot
            slot += duration
