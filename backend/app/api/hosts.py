"""Public pages of a Host: what Guests see. No authentication."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AwareDatetime, BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import get_now
from app.config import settings
from app.db import get_session
from app.models import EventType, Host
from app.schedule import get_schedule
from app.slots import compute_slots

router = APIRouter(prefix="/hosts", tags=["hosts"])


class PublicEventType(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    duration_minutes: int


class PublicHost(BaseModel):
    public_name: str
    handle: str
    event_types: list[PublicEventType]


def get_host_by_handle(handle: str, db: Annotated[Session, Depends(get_session)]) -> Host:
    """FastAPI dependency: the Host of the `{handle}` path parameter, or 404."""
    host = db.scalar(select(Host).where(Host.handle == handle))
    if host is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Host not found")
    return host


HostByHandle = Annotated[Host, Depends(get_host_by_handle)]


@router.get(
    "/{handle}", responses={status.HTTP_404_NOT_FOUND: {"description": "No Host with this Handle"}}
)
def get_public_host(host: HostByHandle, db: Annotated[Session, Depends(get_session)]) -> PublicHost:
    """A Host's Public name and the Event Types Guests can book."""
    event_types = db.scalars(
        select(EventType)
        .where(EventType.host_id == host.id, EventType.archived.is_(False))
        .order_by(EventType.id)
    )
    return PublicHost(
        public_name=host.public_name,
        handle=host.handle,
        event_types=[PublicEventType.model_validate(event_type) for event_type in event_types],
    )


class PublicEventTypeDetail(PublicEventType):
    host_public_name: str


class Slots(BaseModel):
    slots: list[datetime]


def get_bookable_event_type(
    event_type_id: int, host: HostByHandle, db: Annotated[Session, Depends(get_session)]
) -> EventType:
    """FastAPI dependency: an active Event Type of the `{handle}` Host, or 404."""
    event_type = db.get(EventType, event_type_id)
    if event_type is None or event_type.host_id != host.id or event_type.archived:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event Type not found")
    return event_type


BookableEventType = Annotated[EventType, Depends(get_bookable_event_type)]

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"description": "No such Host or bookable Event Type"}}


@router.get("/{handle}/event-types/{event_type_id}", responses=NOT_FOUND)
def get_public_event_type(
    host: HostByHandle, event_type: BookableEventType
) -> PublicEventTypeDetail:
    """An Event Type a Guest can book, with its Host's Public name."""
    return PublicEventTypeDetail(
        id=event_type.id,
        title=event_type.title,
        description=event_type.description,
        duration_minutes=event_type.duration_minutes,
        host_public_name=host.public_name,
    )


@router.get("/{handle}/event-types/{event_type_id}/slots", responses=NOT_FOUND)
def list_slots(
    host: HostByHandle,
    event_type: BookableEventType,
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    start: Annotated[AwareDatetime, Query(alias="from")],
    end: Annotated[AwareDatetime, Query(alias="to")],
) -> Slots:
    """Free Slot start times (UTC) in [from, to), clipped to the booking window."""
    slots = compute_slots(
        schedule=get_schedule(db, host.id),
        time_zone=host.time_zone,
        duration=timedelta(minutes=event_type.duration_minutes),
        now=now,
        window_days=settings.booking_window_days,
        start=start,
        end=end,
    )
    return Slots(slots=slots)
