from collections.abc import Callable
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from tests.api import book, create_event_type, get_slots, set_schedule, sign_up

MONDAY = 0
SUNDAY_NOON = datetime(2026, 1, 4, 12, tzinfo=UTC)
MONDAY_START, MONDAY_END = "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z"

SetNow = Callable[[datetime], None]


def host_with_bookings(client: TestClient, set_now: SetNow, *starts: str) -> int:
    """A Host in UTC working Mondays 09:00-12:00, with Bookings at `starts` (booked on
    Sunday). Returns the Event Type's id."""
    set_now(SUNDAY_NOON)
    sign_up(client, time_zone="UTC")
    set_schedule(client, (MONDAY, "09:00", "12:00"))
    event_type_id = create_event_type(client, title="Intro call", duration_minutes=30)["id"]
    with TestClient(app) as guest:
        for index, start in enumerate(starts):
            response = book(guest, event_type_id, start, guest_name=f"Guest {index}")
            assert response.status_code == 201, response.text
    return event_type_id


def bookings(client: TestClient, scope: str) -> list[dict]:
    response = client.get("/api/me/bookings", params={"scope": scope})
    assert response.status_code == 200, response.text
    return response.json()


def test_host_sees_upcoming_bookings_in_order(client: TestClient, set_now: SetNow) -> None:
    host_with_bookings(client, set_now, "2026-01-05T10:00:00Z", "2026-01-05T09:00:00Z")

    upcoming = bookings(client, "upcoming")

    assert [b["guest_name"] for b in upcoming] == ["Guest 1", "Guest 0"]
    assert upcoming[0] | {"id": 0} == {
        "id": 0,
        "event_type_title": "Intro call",
        "start": "2026-01-05T09:00:00Z",
        "end": "2026-01-05T09:30:00Z",
        "guest_name": "Guest 1",
        "guest_email": "grace@example.com",
        "guest_note": "Let's talk about the project.",
        "status": "active",
        "created_at": upcoming[0]["created_at"],
        "cancelled_at": None,
    }
    assert bookings(client, "past") == []


def test_ended_bookings_move_to_past_newest_first(client: TestClient, set_now: SetNow) -> None:
    host_with_bookings(
        client, set_now, "2026-01-05T09:00:00Z", "2026-01-05T09:30:00Z", "2026-01-05T11:00:00Z"
    )

    set_now(datetime(2026, 1, 5, 10, 0, tzinfo=UTC))

    assert [b["guest_name"] for b in bookings(client, "upcoming")] == ["Guest 2"]
    assert [b["guest_name"] for b in bookings(client, "past")] == ["Guest 1", "Guest 0"]


def test_cancelled_booking_stays_in_history_and_frees_the_slot(
    client: TestClient, set_now: SetNow
) -> None:
    event_type_id = host_with_bookings(client, set_now, "2026-01-05T09:00:00Z")
    booking_id = bookings(client, "upcoming")[0]["id"]
    set_now(datetime(2026, 1, 4, 13, tzinfo=UTC))

    response = client.post(f"/api/me/bookings/{booking_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancelled_at"] == "2026-01-04T13:00:00Z"
    assert bookings(client, "upcoming") == []
    assert [b["status"] for b in bookings(client, "past")] == ["cancelled"]
    assert "2026-01-05T09:00:00Z" in get_slots(client, event_type_id, MONDAY_START, MONDAY_END)
    assert book(client, event_type_id, "2026-01-05T09:00:00Z").status_code == 201


def test_cancelling_twice_changes_nothing(client: TestClient, set_now: SetNow) -> None:
    host_with_bookings(client, set_now, "2026-01-05T09:00:00Z")
    booking_id = bookings(client, "upcoming")[0]["id"]
    first = client.post(f"/api/me/bookings/{booking_id}/cancel").json()
    set_now(datetime(2026, 1, 4, 18, tzinfo=UTC))

    second = client.post(f"/api/me/bookings/{booking_id}/cancel")

    assert second.status_code == 200
    assert second.json() == first


def test_host_cannot_see_or_cancel_another_hosts_bookings(
    client: TestClient, set_now: SetNow
) -> None:
    host_with_bookings(client, set_now, "2026-01-05T09:00:00Z")
    booking_id = bookings(client, "upcoming")[0]["id"]

    with TestClient(app) as other:
        sign_up(other, email="other@example.com", public_name="Other")
        listed = other.get("/api/me/bookings", params={"scope": "upcoming"}).json()
        cancel = other.post(f"/api/me/bookings/{booking_id}/cancel")

    assert listed == []
    assert cancel.status_code == 404
    assert bookings(client, "upcoming")[0]["status"] == "active"


def test_bookings_need_a_session(client: TestClient) -> None:
    assert client.get("/api/me/bookings", params={"scope": "upcoming"}).status_code == 401
    assert client.post("/api/me/bookings/1/cancel").status_code == 401
