"""Public pages of a Host: what Guests see. No authentication."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import EventType, Host

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
