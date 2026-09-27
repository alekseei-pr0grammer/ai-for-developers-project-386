from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_uses_readable_operation_ids() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert paths["/api/health"]["get"]["operationId"] == "get_health"


def test_readiness_reports_database_ok() -> None:
    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
