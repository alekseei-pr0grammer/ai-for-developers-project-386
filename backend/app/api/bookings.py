from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.errors import ExclusionViolation
from pydantic import AwareDatetime, BaseModel, EmailStr, StringConstraints
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.hosts import BookableEventType, HostByHandle
from app.auth import CurrentHost
from app.clock import get_now
from app.config import settings
from app.db import get_session
from app.models import Booking, EventType
from app.schedule import get_schedule
from app.slots import compute_slots

public_router = APIRouter(prefix="/hosts/{handle}/event-types/{event_type_id}", tags=["bookings"])
host_router = APIRouter(prefix="/me/bookings", tags=["bookings"])

GuestName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
GuestNote = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class BookingRequest(BaseModel):
    start: AwareDatetime
    guest_name: GuestName
    guest_email: EmailStr
    guest_note: GuestNote = ""


class BookingConfirmation(BaseModel):
    id: int
    start: datetime
    end: datetime
    event_type_title: str
    host_public_name: str
    guest_name: str
    guest_email: str
    guest_note: str


@public_router.post(
    "/bookings",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No such Host or bookable Event Type"},
        status.HTTP_409_CONFLICT: {"description": "The time was just taken by another Booking"},
    },
)
def create_booking(
    body: BookingRequest,
    host: HostByHandle,
    event_type: BookableEventType,
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> BookingConfirmation:
    """Book a Slot as a Guest. No account needed (ADR 0002)."""
    duration = timedelta(minutes=event_type.duration_minutes)
    # Existing Bookings are left out here on purpose: whether the time is still free
    # is decided by the database constraint below, which also covers concurrent requests.
    offered = compute_slots(
        schedule=get_schedule(db, host.id),
        time_zone=host.time_zone,
        duration=duration,
        now=now,
        window_days=settings.booking_window_days,
        start=body.start,
        end=body.start + timedelta(microseconds=1),
    )
    if not offered:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "This time is not bookable")

    booking = Booking(
        host_id=host.id,
        event_type_id=event_type.id,
        start_at=body.start,
        end_at=body.start + duration,
        guest_name=body.guest_name,
        guest_email=str(body.guest_email),
        guest_note=body.guest_note,
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if isinstance(exc.orig, ExclusionViolation):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Sorry, this time was just booked. Please pick another."
            ) from exc
        raise

    return BookingConfirmation(
        id=booking.id,
        start=booking.start_at,
        end=booking.end_at,
        event_type_title=event_type.title,
        host_public_name=host.public_name,
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        guest_note=booking.guest_note,
    )


class HostBooking(BaseModel):
    id: int
    event_type_title: str
    start: datetime
    end: datetime
    guest_name: str
    guest_email: str
    guest_note: str
    status: Literal["active", "cancelled"]
    created_at: datetime
    cancelled_at: datetime | None


def _host_booking(booking: Booking, event_type_title: str) -> HostBooking:
    return HostBooking(
        id=booking.id,
        event_type_title=event_type_title,
        start=booking.start_at,
        end=booking.end_at,
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        guest_note=booking.guest_note,
        status=booking.status,
        created_at=booking.created_at,
        cancelled_at=booking.cancelled_at,
    )


@host_router.get("")
def list_my_bookings(
    scope: Literal["upcoming", "past"],
    host: CurrentHost,
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> list[HostBooking]:
    """Upcoming: active and not yet ended, soonest first.
    Past: ended or cancelled, most recent first."""
    query = (
        select(Booking, EventType.title)
        .join(EventType, EventType.id == Booking.event_type_id)
        .where(Booking.host_id == host.id)
    )
    if scope == "upcoming":
        query = query.where(Booking.status == "active", Booking.end_at > now).order_by(
            Booking.start_at
        )
    else:
        query = query.where(or_(Booking.status == "cancelled", Booking.end_at <= now)).order_by(
            Booking.start_at.desc()
        )
    return [_host_booking(booking, title) for booking, title in db.execute(query)]


@host_router.post(
    "/{booking_id}/cancel",
    responses={status.HTTP_404_NOT_FOUND: {"description": "No such Booking of this Host"}},
)
def cancel_booking(
    booking_id: int,
    host: CurrentHost,
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> HostBooking:
    """Cancel a Booking: it stays in history as cancelled and its time is free again.
    Cancelling a cancelled Booking changes nothing."""
    booking = db.get(Booking, booking_id)
    if booking is None or booking.host_id != host.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status == "active":
        booking.status = "cancelled"
        booking.cancelled_at = now
        db.commit()
    return _host_booking(booking, db.get_one(EventType, booking.event_type_id).title)
