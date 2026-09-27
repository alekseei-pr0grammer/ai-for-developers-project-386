from datetime import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.auth import CurrentHost
from app.db import get_session
from app.schedule import get_schedule, replace_schedule

router = APIRouter(prefix="/me/schedule", tags=["schedule"])


class ScheduleIntervalModel(BaseModel):
    """Local wall-clock hours on a weekday, in the Host's time zone."""

    weekday: Annotated[int, Field(ge=0, le=6, description="0 = Monday ... 6 = Sunday")]
    start: time
    end: time

    @model_validator(mode="after")
    def end_after_start(self) -> ScheduleIntervalModel:
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class WeeklySchedule(BaseModel):
    intervals: list[ScheduleIntervalModel]

    @model_validator(mode="after")
    def no_overlaps(self) -> WeeklySchedule:
        ordered = sorted(self.intervals, key=lambda i: (i.weekday, i.start))
        for previous, current in zip(ordered, ordered[1:], strict=False):
            if previous.weekday == current.weekday and current.start < previous.end:
                raise ValueError("intervals on the same weekday must not overlap")
        return self


def _response(db: Session, host_id: int) -> WeeklySchedule:
    return WeeklySchedule(
        intervals=[
            ScheduleIntervalModel(weekday=weekday, start=start, end=end)
            for weekday, start, end in get_schedule(db, host_id)
        ]
    )


@router.get("")
def get_my_schedule(
    host: CurrentHost, db: Annotated[Session, Depends(get_session)]
) -> WeeklySchedule:
    """The Host's Weekly Schedule, ordered by weekday and start."""
    return _response(db, host.id)


@router.put("")
def replace_my_schedule(
    body: WeeklySchedule, host: CurrentHost, db: Annotated[Session, Depends(get_session)]
) -> WeeklySchedule:
    """Replace the whole Weekly Schedule at once."""
    replace_schedule(db, host.id, [(i.weekday, i.start, i.end) for i in body.intervals])
    db.commit()
    return _response(db, host.id)
