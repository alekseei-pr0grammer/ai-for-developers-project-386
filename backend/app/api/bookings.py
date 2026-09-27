from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.errors import ExclusionViolation
from pydantic import AwareDatetime, BaseModel, EmailStr, StringConstraints
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.hosts import BookableEventType, HostByHandle
from app.clock import get_now
from app.config import settings
from app.db import get_session
from app.models import Booking
from app.schedule import get_schedule
from app.slots import compute_slots

public_router = APIRouter(prefix="/hosts/{handle}/event-types/{event_type_id}", tags=["bookings"])

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
