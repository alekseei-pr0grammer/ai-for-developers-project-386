import pytest

from app.config import Settings


@pytest.mark.parametrize(
    "given",
    [
        # Render's and most hosts' connection strings.
        "postgresql://user:pw@host:5432/db",
        "postgres://user:pw@host:5432/db",
        # Already naming our driver.
        "postgresql+psycopg://user:pw@host:5432/db",
    ],
)
def test_database_url_uses_the_psycopg_driver(given: str) -> None:
    settings = Settings(database_url=given)

    assert settings.database_url == "postgresql+psycopg://user:pw@host:5432/db"
