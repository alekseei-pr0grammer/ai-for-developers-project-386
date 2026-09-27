from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.fields import PublicName, TimeZone
from app.api.me import HostResponse
from app.auth import SESSION_COOKIE, end_session, hash_password, start_session, verify_password
from app.clock import get_now
from app.db import get_session
from app.handles import derive_handle
from app.models import Host

router = APIRouter(prefix="/auth", tags=["auth"])

# A concurrent sign-up can take the Handle we derived; derive again this many times.
HANDLE_ATTEMPTS = 5


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    public_name: PublicName
    time_zone: TimeZone


class LogInRequest(BaseModel):
    email: EmailStr
    password: str


def _email_taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "This email is already registered")


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"description": "Email already registered"}},
)
def sign_up(
    body: SignUpRequest,
    response: Response,
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> HostResponse:
    """Create a Host account and log it in."""
    email = body.email.lower()
    if db.scalar(select(Host.id).where(Host.email == email)) is not None:
        raise _email_taken()
    password_hash = hash_password(body.password)
    for _ in range(HANDLE_ATTEMPTS):
        host = Host(
            email=email,
            password_hash=password_hash,
            public_name=body.public_name,
            handle=derive_handle(db, body.public_name),
            time_zone=body.time_zone,
        )
        db.add(host)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if db.scalar(select(Host.id).where(Host.email == email)) is not None:
                raise _email_taken() from None
    else:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Please try again")
    start_session(db, host, response, now)
    return HostResponse.model_validate(host, from_attributes=True)


@router.post(
    "/login",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Wrong email or password"}},
)
def log_in(
    body: LogInRequest,
    response: Response,
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> HostResponse:
    """Log a Host in with email and password."""
    host = db.scalar(select(Host).where(Host.email == body.email.lower()))
    if not verify_password(host.password_hash if host else None, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    start_session(db, host, response, now)
    return HostResponse.model_validate(host, from_attributes=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def log_out(
    response: Response,
    db: Annotated[Session, Depends(get_session)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    """End the current session, if any."""
    end_session(db, session, response)
