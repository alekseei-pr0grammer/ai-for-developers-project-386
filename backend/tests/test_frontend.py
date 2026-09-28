from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

INDEX = "<!doctype html><div id='root'></div>"


@pytest.fixture
def frontend_client(tmp_path: Path) -> TestClient:
    """The API serving a built frontend: an app page, a hashed asset and a public file."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(INDEX)
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log('app')")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    return TestClient(create_app(frontend_dist=tmp_path))


@pytest.mark.parametrize("path", ["/", "/alex-alekseev", "/alex-alekseev/1", "/dashboard"])
def test_frontend_routes_get_the_app_page(frontend_client: TestClient, path: str) -> None:
    response = frontend_client.get(path)

    assert response.status_code == 200
    assert response.text == INDEX
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-cache"


def test_built_assets_are_served_and_cached_forever(frontend_client: TestClient) -> None:
    response = frontend_client.get("/assets/index-abc123.js")

    assert response.status_code == 200
    assert response.text == "console.log('app')"
    assert "javascript" in response.headers["content-type"]
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_other_built_files_are_served(frontend_client: TestClient) -> None:
    response = frontend_client.get("/favicon.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")


def test_missing_asset_is_a_404_not_the_app_page(frontend_client: TestClient) -> None:
    assert frontend_client.get("/assets/missing.js").status_code == 404


def test_files_outside_the_build_are_not_reachable(frontend_client: TestClient) -> None:
    response = frontend_client.get("/..%2F..%2Fetc%2Fpasswd")

    assert response.status_code == 200
    assert response.text == INDEX


def test_api_still_works_next_to_the_frontend(frontend_client: TestClient) -> None:
    assert frontend_client.get("/api/health").json() == {"status": "ok"}


def test_unknown_api_path_is_a_json_404(frontend_client: TestClient) -> None:
    response = frontend_client.get("/api/nope")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_without_a_build_only_the_api_is_served(tmp_path: Path) -> None:
    client = TestClient(create_app(frontend_dist=None))

    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 404


def test_api_docs_are_not_shadowed_by_the_frontend(frontend_client: TestClient) -> None:
    assert "swagger" in frontend_client.get("/docs").text.lower()
    assert frontend_client.get("/openapi.json").json()["info"]["title"] == "Calendar API"
