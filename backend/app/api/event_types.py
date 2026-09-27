from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import CurrentHost
from app.db import get_session
from app.models import EventType

router = APIRouter(prefix="/me/event-types", tags=["event types"])

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
DurationMinutes = Annotated[int, Field(gt=0, le=720)]


class EventTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    duration_minutes: int
    archived: bool


class EventTypeCreate(BaseModel):
    title: Title
    description: Description = ""
    duration_minutes: DurationMinutes


class EventTypeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    description: Description | None = None
    duration_minutes: DurationMinutes | None = None
    archived: bool | None = None


@router.get("")
def list_my_event_types(
    host: CurrentHost, db: Annotated[Session, Depends(get_session)]
) -> list[EventTypeResponse]:
    """All of the Host's Event Types, archived ones included, oldest first."""
    event_types = db.scalars(
        select(EventType).where(EventType.host_id == host.id).order_by(EventType.id)
    )
    return [EventTypeResponse.model_validate(event_type) for event_type in event_types]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event_type(
    body: EventTypeCreate, host: CurrentHost, db: Annotated[Session, Depends(get_session)]
) -> EventTypeResponse:
    event_type = EventType(host_id=host.id, **body.model_dump())
    db.add(event_type)
    db.commit()
    return EventTypeResponse.model_validate(event_type)


@router.patch(
    "/{event_type_id}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "No such Event Type of this Host"}},
)
def update_event_type(
    event_type_id: int,
    body: EventTypeUpdate,
    host: CurrentHost,
    db: Annotated[Session, Depends(get_session)],
) -> EventTypeResponse:
    """Edit or (un)archive an Event Type. Existing Bookings keep their own start and end."""
    event_type = db.get(EventType, event_type_id)
    if event_type is None or event_type.host_id != host.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event Type not found")
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(event_type, field, value)
    db.commit()
    return EventTypeResponse.model_validate(event_type)
