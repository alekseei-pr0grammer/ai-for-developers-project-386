"""Host authentication: password hashing, sessions and the session cookie."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.clock import get_now
from app.config import settings
from app.db import get_session
from app.models import Host, HostSession

SESSION_COOKIE = "session"

_hasher = PasswordHasher()
# Verified against when the email is unknown, so a failed login takes the same
# time whether or not the account exists.
_DUMMY_HASH = _hasher.hash("not a real password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Check a password. Pass None for an unknown account: still costs one verification."""
    try:
        _hasher.verify(password_hash or _DUMMY_HASH, password)
    except VerificationError:
        return False
    return password_hash is not None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(db: Session, host: Host, response: Response, now: datetime) -> None:
    """Create a session for the Host and set its cookie on the response."""
    token = secrets.token_urlsafe(32)
    lifetime = timedelta(days=settings.session_lifetime_days)
    db.add(HostSession(host_id=host.id, token_hash=_hash_token(token), expires_at=now + lifetime))
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )


def end_session(db: Session, token: str | None, response: Response) -> None:
    if token:
        db.execute(delete(HostSession).where(HostSession.token_hash == _hash_token(token)))
        db.commit()
    response.delete_cookie(
        SESSION_COOKIE, httponly=True, secure=settings.session_cookie_secure, samesite="lax"
    )


def get_current_host(
    db: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Host:
    """FastAPI dependency: the logged-in Host, or 401."""
    host = None
    if session:
        host = db.scalar(
            select(Host)
            .join(HostSession, HostSession.host_id == Host.id)
            .where(HostSession.token_hash == _hash_token(session), HostSession.expires_at > now)
        )
    if host is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    return host


CurrentHost = Annotated[Host, Depends(get_current_host)]
