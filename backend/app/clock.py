from datetime import UTC, datetime


def get_now() -> datetime:
    """FastAPI dependency: the current time, timezone-aware UTC.

    Endpoints that depend on "now" take it through this dependency, so tests can
    freeze it (see the `set_now` fixture).
    """
    return datetime.now(UTC)
