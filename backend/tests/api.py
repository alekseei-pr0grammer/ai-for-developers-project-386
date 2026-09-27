"""Helpers that set up state through the API, the same way a Host would."""

from typing import Any

from fastapi.testclient import TestClient
from httpx import Response


def sign_up(client: TestClient, **overrides: str) -> Response:
    payload = {
        "email": "alex@example.com",
        "password": "correct horse battery",
        "public_name": "Alex Alekseev",
        "time_zone": "Europe/London",
    } | overrides
    return client.post("/api/auth/signup", json=payload)


def create_event_type(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Intro call",
        "description": "A quick first chat.",
        "duration_minutes": 30,
    } | overrides
    response = client.post("/api/me/event-types", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
