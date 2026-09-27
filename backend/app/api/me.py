from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.fields import PublicName, TimeZone
from app.auth import CurrentHost
from app.db import get_session

router = APIRouter(prefix="/me", tags=["me"])


class HostResponse(BaseModel):
    email: str
    public_name: str
    handle: str
    time_zone: str


class HostUpdate(BaseModel):
    # Unknown fields are rejected: in particular the Handle, which never changes (ADR 0001).
    model_config = ConfigDict(extra="forbid")

    public_name: PublicName | None = None
    time_zone: TimeZone | None = None


@router.get("")
def get_me(host: CurrentHost) -> HostResponse:
    """The logged-in Host."""
    return HostResponse.model_validate(host, from_attributes=True)


@router.patch("")
def update_me(
    body: HostUpdate, host: CurrentHost, db: Annotated[Session, Depends(get_session)]
) -> HostResponse:
    """Change the Host's Public name and/or time zone. The Handle stays the same."""
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(host, field, value)
    db.commit()
    return HostResponse.model_validate(host, from_attributes=True)
