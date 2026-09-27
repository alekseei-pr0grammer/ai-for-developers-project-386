"""Bookings: reservations of a Host's time."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking


def busy_ranges(db: Session, host_id: int, after: datetime) -> list[tuple[datetime, datetime]]:
    """(start, end) of the Host's active Bookings that end after `after`."""
    rows = db.execute(
        select(Booking.start_at, Booking.end_at).where(
            Booking.host_id == host_id, Booking.status == "active", Booking.end_at > after
        )
    )
    return [(start, end) for start, end in rows]
