"""Test harness: the API is tested over HTTP against a real, migrated Postgres database.

Tests use a separate database (TEST_DATABASE_URL, default `calendar_test` on the local
`make db` server), so running them never touches development data.
"""

import os
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://calendar:calendar@localhost:5432/calendar_test",
)
# Must be set before the app is imported: its engine and settings read it at import time.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
# TestClient talks plain HTTP, which would drop a Secure cookie.
os.environ["SESSION_COOKIE_SECURE"] = "false"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.clock import get_now  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _create_database_if_missing() -> None:
    url = make_url(TEST_DATABASE_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Create the test database and migrate it to head, once per run."""
    _create_database_if_missing()
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")


@pytest.fixture(autouse=True)
def empty_tables() -> Iterator[None]:
    """Each test starts from empty tables. Truncating (rather than rolling back a
    transaction) keeps tests realistic: requests commit, and concurrent requests
    see each other's data just as they would in production."""
    yield
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    if tables:
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def set_now() -> Iterator[Callable[[datetime], None]]:
    """Freeze the API's clock: `set_now(datetime(2026, 1, 5, 9, tzinfo=UTC))`."""
    now = datetime.now(UTC)

    def override() -> datetime:
        return now

    def set_(value: datetime) -> None:
        nonlocal now
        now = value

    app.dependency_overrides[get_now] = override
    yield set_
    app.dependency_overrides.pop(get_now, None)
