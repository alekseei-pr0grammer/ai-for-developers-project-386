import threading
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from tests.api import book, create_event_type, get_slots, set_schedule, sign_up

MONDAY = 0
SUNDAY_NOON = datetime(2026, 1, 4, 12, tzinfo=UTC)
MONDAY_START, MONDAY_END = "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z"

SetNow = Callable[[datetime], None]


def host_with_monday_morning(client: TestClient, set_now: SetNow, **event_type: object) -> int:
    """A Host in UTC who works Mondays 09:00-11:00; returns a new Event Type's id."""
    set_now(SUNDAY_NOON)
    sign_up(client, time_zone="UTC")
    set_schedule(client, (MONDAY, "09:00", "11:00"))
    return create_event_type(client, **({"duration_minutes": 30} | event_type))["id"]


def test_guest_books_an_offered_slot(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now, title="Intro call")

    with TestClient(app) as guest:
        response = book(guest, event_type_id, "2026-01-05T09:30:00Z")

    assert response.status_code == 201
    assert response.json() | {"id": 0} == {
        "id": 0,
        "start": "2026-01-05T09:30:00Z",
        "end": "2026-01-05T10:00:00Z",
        "event_type_title": "Intro call",
        "host_public_name": "Alex Alekseev",
        "guest_name": "Grace Guest",
        "guest_email": "grace@example.com",
        "guest_note": "Let's talk about the project.",
    }


def test_booked_time_is_no_longer_offered(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now)

    book(client, event_type_id, "2026-01-05T09:30:00Z")

    assert get_slots(client, event_type_id, MONDAY_START, MONDAY_END) == [
        "2026-01-05T09:00:00Z",
        "2026-01-05T10:00:00Z",
        "2026-01-05T10:30:00Z",
    ]


def test_booking_blocks_time_across_all_event_types(client: TestClient, set_now: SetNow) -> None:
    short = host_with_monday_morning(client, set_now, duration_minutes=30)
    long = create_event_type(client, duration_minutes=60)["id"]

    assert book(client, short, "2026-01-05T09:30:00Z").status_code == 201

    # A 60-minute call at 09:00 would overlap the 09:30-10:00 Booking.
    assert get_slots(client, long, MONDAY_START, MONDAY_END) == ["2026-01-05T10:00:00Z"]
    assert book(client, long, "2026-01-05T09:00:00Z").status_code == 409


def test_same_slot_cannot_be_booked_twice(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now)
    book(client, event_type_id, "2026-01-05T09:00:00Z")

    response = book(client, event_type_id, "2026-01-05T09:00:00Z", guest_email="x@example.com")

    assert response.status_code == 409


def test_back_to_back_bookings_are_allowed(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now)

    first = book(client, event_type_id, "2026-01-05T09:00:00Z")
    second = book(client, event_type_id, "2026-01-05T09:30:00Z")

    assert first.status_code == second.status_code == 201


def test_concurrent_requests_for_one_slot_only_one_wins(
    client: TestClient, set_now: SetNow
) -> None:
    event_type_id = host_with_monday_morning(client, set_now)
    barrier = threading.Barrier(2)
    statuses: list[int] = []

    def attempt(email: str) -> None:
        with TestClient(app) as guest:
            barrier.wait()
            statuses.append(
                book(guest, event_type_id, "2026-01-05T10:00:00Z", guest_email=email).status_code
            )

    threads = [threading.Thread(target=attempt, args=(f"g{i}@example.com",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(statuses) == [201, 409]


def test_start_must_be_an_offered_slot(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now)

    off_grid = book(client, event_type_id, "2026-01-05T09:10:00Z")
    outside_hours = book(client, event_type_id, "2026-01-05T15:00:00Z")
    in_the_past = book(client, event_type_id, "2026-01-01T09:00:00Z")

    assert off_grid.status_code == outside_hours.status_code == in_the_past.status_code == 422


def test_guest_details_are_validated(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now)

    no_name = book(client, event_type_id, "2026-01-05T09:00:00Z", guest_name=" ")
    bad_email = book(client, event_type_id, "2026-01-05T09:00:00Z", guest_email="not-an-email")

    assert no_name.status_code == bad_email.status_code == 422


def test_note_is_optional(client: TestClient, set_now: SetNow) -> None:
    event_type_id = host_with_monday_morning(client, set_now)

    response = client.post(
        f"/api/hosts/alex-alekseev/event-types/{event_type_id}/bookings",
        json={
            "start": "2026-01-05T09:00:00Z",
            "guest_name": "Grace",
            "guest_email": "grace@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["guest_note"] == ""


def test_host_booking_another_host_keeps_own_time_free(client: TestClient, set_now: SetNow) -> None:
    alex_event_type = host_with_monday_morning(client, set_now)
    with TestClient(app) as bea:
        sign_up(bea, email="bea@example.com", public_name="Bea", time_zone="UTC")
        set_schedule(bea, (MONDAY, "09:00", "11:00"))
        bea_event_type = create_event_type(bea, duration_minutes=30)["id"]

        # Alex books Bea, as a Guest.
        response = book(
            client,
            bea_event_type,
            "2026-01-05T09:00:00Z",
            handle="bea",
            guest_email="alex@example.com",
        )

    assert response.status_code == 201
    assert get_slots(client, alex_event_type, MONDAY_START, MONDAY_END)[0] == "2026-01-05T09:00:00Z"
