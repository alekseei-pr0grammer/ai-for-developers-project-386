"""Validated field types shared by several API models."""

from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, StringConstraints


def _check_time_zone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown time zone: {value!r}") from exc
    return value


# An IANA time zone name, e.g. "Europe/London".
TimeZone = Annotated[str, AfterValidator(_check_time_zone)]

PublicName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
