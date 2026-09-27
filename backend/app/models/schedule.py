from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ScheduleInterval(Base):
    """One interval of a Host's Weekly Schedule: local wall-clock hours on a weekday,
    in the Host's time zone. A weekday without intervals is a day off."""

    __tablename__ = "schedule_intervals"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_valid"),
        CheckConstraint("end_time > start_time", name="end_after_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    # 0 = Monday ... 6 = Sunday, like Python's date.weekday().
    weekday: Mapped[int] = mapped_column(SmallInteger)
    start_time: Mapped[time]
    end_time: Mapped[time]
