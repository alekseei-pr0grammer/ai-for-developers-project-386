from datetime import datetime
from typing import Literal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

BookingStatus = Literal["active", "cancelled"]


class Booking(Base):
    """A Guest's reservation of a Host's time for one Event Type.

    A Guest is not stored on its own (ADR 0002): just the name, email and note given here.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="end_after_start"),
        CheckConstraint("status IN ('active', 'cancelled')", name="status_valid"),
        # A Host's active Bookings never overlap, across all their Event Types (ADR 0003).
        # Half-open ranges, so back-to-back Bookings are fine. Needs btree_gist for `=`.
        ExcludeConstraint(
            ("host_id", "="),
            (text("tstzrange(start_at, end_at, '[)')"), "&&"),
            using="gist",
            where=text("status = 'active'"),
            name="bookings_no_overlap",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # The booked Host (denormalised from the Event Type so the constraint fits one table).
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    event_type_id: Mapped[int] = mapped_column(ForeignKey("event_types.id", ondelete="CASCADE"))
    # Stored, not derived from the Event Type, so later duration changes don't move it.
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    guest_name: Mapped[str] = mapped_column(String(100))
    guest_email: Mapped[str] = mapped_column(String(320))
    guest_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
