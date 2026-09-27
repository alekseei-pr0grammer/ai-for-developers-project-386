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


def set_schedule(client: TestClient, *intervals: tuple[int, str, str]) -> None:
    """Replace the logged-in Host's Weekly Schedule: set_schedule(client, (0, "09:00", "12:00"))."""
    body = {"intervals": [{"weekday": w, "start": s, "end": e} for w, s, e in intervals]}
    response = client.put("/api/me/schedule", json=body)
    assert response.status_code == 200, response.text


def get_slots(
    client: TestClient, event_type_id: int, start: str, end: str, handle: str = "alex-alekseev"
) -> list[str]:
    response = client.get(
        f"/api/hosts/{handle}/event-types/{event_type_id}/slots",
        params={"from": start, "to": end},
    )
    assert response.status_code == 200, response.text
    return response.json()["slots"]


def book(
    client: TestClient,
    event_type_id: int,
    start: str,
    handle: str = "alex-alekseev",
    **overrides: Any,
) -> Response:
    payload = {
        "start": start,
        "guest_name": "Grace Guest",
        "guest_email": "grace@example.com",
        "guest_note": "Let's talk about the project.",
    } | overrides
    return client.post(f"/api/hosts/{handle}/event-types/{event_type_id}/bookings", json=payload)
