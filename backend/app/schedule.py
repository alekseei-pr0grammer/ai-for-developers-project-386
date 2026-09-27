"""The Weekly Schedule: when a Host accepts Bookings."""

from datetime import time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import ScheduleInterval

# (weekday, start, end); weekday 0 = Monday.
Interval = tuple[int, time, time]

# New Hosts accept Bookings Monday to Friday, 09:00-17:00 in their time zone.
DEFAULT_SCHEDULE: list[Interval] = [(weekday, time(9), time(17)) for weekday in range(5)]


def get_schedule(db: Session, host_id: int) -> list[Interval]:
    """The Host's intervals, ordered by weekday and start."""
    rows = db.scalars(
        select(ScheduleInterval)
        .where(ScheduleInterval.host_id == host_id)
        .order_by(ScheduleInterval.weekday, ScheduleInterval.start_time)
    )
    return [(row.weekday, row.start_time, row.end_time) for row in rows]


def replace_schedule(db: Session, host_id: int, intervals: list[Interval]) -> None:
    """Replace the whole Weekly Schedule. The caller commits."""
    db.execute(delete(ScheduleInterval).where(ScheduleInterval.host_id == host_id))
    db.add_all(
        ScheduleInterval(host_id=host_id, weekday=weekday, start_time=start, end_time=end)
        for weekday, start, end in intervals
    )
