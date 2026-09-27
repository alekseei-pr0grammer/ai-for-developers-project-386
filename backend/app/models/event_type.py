from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EventType(Base):
    """A kind of meeting a Host offers, with a fixed duration."""

    __tablename__ = "event_types"
    __table_args__ = (CheckConstraint("duration_minutes > 0", name="duration_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    duration_minutes: Mapped[int]
    # Archived Event Types can't be booked; their past Bookings stay.
    archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
