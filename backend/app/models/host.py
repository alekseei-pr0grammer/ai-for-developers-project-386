from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Host(Base):
    """A person with an account who offers Event Types and receives Bookings."""

    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored lowercased, so uniqueness is case-insensitive.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    public_name: Mapped[str] = mapped_column(String(100))
    # Permanent: derived from the Public name at sign-up, never changed (ADR 0001).
    handle: Mapped[str] = mapped_column(String(60), unique=True)
    # IANA time zone name, e.g. "Europe/London"; the Weekly Schedule is in this zone.
    time_zone: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HostSession(Base):
    """A logged-in browser of a Host. Only a hash of the cookie token is stored."""

    __tablename__ = "host_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
