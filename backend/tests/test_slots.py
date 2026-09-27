from collections.abc import Callable
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from tests.api import create_event_type, get_slots, set_schedule, sign_up

MONDAY = 0
# 2026-01-04 is a Sunday; 2026-01-05 the Monday after.
SUNDAY_NOON = datetime(2026, 1, 4, 12, tzinfo=UTC)

SetNow = Callable[[datetime], None]


def test_slots_step_by_duration_and_fit_inside_the_schedule(
    client: TestClient, set_now: SetNow
) -> None:
    set_now(SUNDAY_NOON)
    sign_up(client, time_zone="UTC")
    set_schedule(client, (MONDAY, "09:00", "11:00"))
    event_type = create_event_type(client, duration_minutes=45)

    slots = get_slots(client, event_type["id"], "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z")

    # 10:30 would end at 11:15, past the end of the schedule.
    assert slots == ["2026-01-05T09:00:00Z", "2026-01-05T09:45:00Z"]


def test_slots_restart_at_each_interval(client: TestClient, set_now: SetNow) -> None:
    set_now(SUNDAY_NOON)
    sign_up(client, time_zone="UTC")
    set_schedule(client, (MONDAY, "09:00", "10:00"), (MONDAY, "14:30", "15:30"))
    event_type = create_event_type(client, duration_minutes=30)

    slots = get_slots(client, event_type["id"], "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z")

    assert slots == [
        "2026-01-05T09:00:00Z",
        "2026-01-05T09:30:00Z",
        "2026-01-05T14:30:00Z",
        "2026-01-05T15:00:00Z",
    ]


def test_no_slots_in_the_past(client: TestClient, set_now: SetNow) -> None:
    set_now(datetime(2026, 1, 5, 9, 40, tzinfo=UTC))
    sign_up(client, time_zone="UTC")
    set_schedule(client, (MONDAY, "09:00", "11:00"))
    event_type = create_event_type(client, duration_minutes=30)

    slots = get_slots(client, event_type["id"], "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z")

    assert slots == ["2026-01-05T10:00:00Z", "2026-01-05T10:30:00Z"]


def test_slots_only_within_the_next_14_days(client: TestClient, set_now: SetNow) -> None:
    set_now(SUNDAY_NOON)
    sign_up(client, time_zone="UTC")
    set_schedule(client, (MONDAY, "09:00", "10:00"))
    event_type = create_event_type(client, duration_minutes=60)

    slots = get_slots(client, event_type["id"], "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z")

    # Sunday 4th to Saturday 17th; Monday the 19th is too far ahead.
    assert slots == ["2026-01-05T09:00:00Z", "2026-01-12T09:00:00Z"]


def test_slots_follow_the_hosts_time_zone(client: TestClient, set_now: SetNow) -> None:
    set_now(SUNDAY_NOON)
    sign_up(client, time_zone="Asia/Tokyo")
    set_schedule(client, (MONDAY, "09:00", "10:00"))
    event_type = create_event_type(client, duration_minutes=60)

    slots = get_slots(client, event_type["id"], "2026-01-04T00:00:00Z", "2026-01-06T00:00:00Z")

    # 09:00 in Tokyo (UTC+9) is midnight UTC.
    assert slots == ["2026-01-05T00:00:00Z"]


def test_slots_follow_daylight_saving_changes(client: TestClient, set_now: SetNow) -> None:
    # London moves to summer time (UTC+1) on Sunday 2026-03-29.
    set_now(datetime(2026, 3, 26, tzinfo=UTC))
    sign_up(client, time_zone="Europe/London")
    set_schedule(client, (4, "09:00", "10:00"), (MONDAY, "09:00", "10:00"))
    event_type = create_event_type(client, duration_minutes=60)

    slots = get_slots(client, event_type["id"], "2026-03-26T00:00:00Z", "2026-03-31T00:00:00Z")

    assert slots == ["2026-03-27T09:00:00Z", "2026-03-30T08:00:00Z"]


def test_guest_sees_event_type_with_host_name(client: TestClient) -> None:
    sign_up(client)
    event_type = create_event_type(client, title="Intro call", duration_minutes=15)

    with TestClient(app) as guest:
        response = guest.get(f"/api/hosts/alex-alekseev/event-types/{event_type['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "id": event_type["id"],
        "title": "Intro call",
        "description": "A quick first chat.",
        "duration_minutes": 15,
        "host_public_name": "Alex Alekseev",
    }


def test_archived_or_foreign_event_types_are_not_bookable(client: TestClient) -> None:
    sign_up(client)
    archived = create_event_type(client)
    client.patch(f"/api/me/event-types/{archived['id']}", json={"archived": True})
    with TestClient(app) as other:
        sign_up(other, email="other@example.com", public_name="Other")
        foreign = create_event_type(other)

    for event_type_id in (archived["id"], foreign["id"]):
        detail = client.get(f"/api/hosts/alex-alekseev/event-types/{event_type_id}")
        slots = client.get(
            f"/api/hosts/alex-alekseev/event-types/{event_type_id}/slots",
            params={"from": "2026-01-01T00:00:00Z", "to": "2026-01-02T00:00:00Z"},
        )
        assert detail.status_code == slots.status_code == 404


def test_slot_range_must_be_timezone_aware(client: TestClient) -> None:
    sign_up(client)
    event_type = create_event_type(client)

    response = client.get(
        f"/api/hosts/alex-alekseev/event-types/{event_type['id']}/slots",
        params={"from": "2026-01-05T00:00:00", "to": "2026-01-06T00:00:00"},
    )

    assert response.status_code == 422
