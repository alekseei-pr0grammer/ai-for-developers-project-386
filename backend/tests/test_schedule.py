from fastapi.testclient import TestClient

from app.main import app
from tests.api import sign_up

WEEKDAYS_9_TO_5 = [
    {"weekday": weekday, "start": "09:00:00", "end": "17:00:00"} for weekday in range(5)
]


def test_new_host_accepts_bookings_weekdays_nine_to_five(client: TestClient) -> None:
    sign_up(client)

    response = client.get("/api/me/schedule")

    assert response.status_code == 200
    assert response.json() == {"intervals": WEEKDAYS_9_TO_5}


def test_host_replaces_weekly_schedule(client: TestClient) -> None:
    sign_up(client)
    schedule = {
        "intervals": [
            {"weekday": 2, "start": "14:00", "end": "18:00"},
            {"weekday": 2, "start": "09:00", "end": "12:00"},
            {"weekday": 5, "start": "10:00", "end": "11:30"},
        ]
    }

    response = client.put("/api/me/schedule", json=schedule)

    expected = {
        "intervals": [
            {"weekday": 2, "start": "09:00:00", "end": "12:00:00"},
            {"weekday": 2, "start": "14:00:00", "end": "18:00:00"},
            {"weekday": 5, "start": "10:00:00", "end": "11:30:00"},
        ]
    }
    assert response.status_code == 200
    assert response.json() == expected
    assert client.get("/api/me/schedule").json() == expected


def test_host_can_take_every_day_off(client: TestClient) -> None:
    sign_up(client)

    client.put("/api/me/schedule", json={"intervals": []})

    assert client.get("/api/me/schedule").json() == {"intervals": []}


def test_invalid_schedule_is_rejected_and_nothing_is_saved(client: TestClient) -> None:
    sign_up(client)
    end_before_start = [{"weekday": 0, "start": "12:00", "end": "09:00"}]
    overlapping = [
        {"weekday": 1, "start": "09:00", "end": "12:00"},
        {"weekday": 1, "start": "11:00", "end": "13:00"},
    ]
    bad_weekday = [{"weekday": 7, "start": "09:00", "end": "12:00"}]

    for intervals in (end_before_start, overlapping, bad_weekday):
        response = client.put("/api/me/schedule", json={"intervals": intervals})
        assert response.status_code == 422, intervals

    assert client.get("/api/me/schedule").json() == {"intervals": WEEKDAYS_9_TO_5}


def test_back_to_back_intervals_are_allowed(client: TestClient) -> None:
    sign_up(client)
    intervals = [
        {"weekday": 0, "start": "09:00", "end": "12:00"},
        {"weekday": 0, "start": "12:00", "end": "15:00"},
    ]

    assert client.put("/api/me/schedule", json={"intervals": intervals}).status_code == 200


def test_schedule_is_private_to_its_host(client: TestClient) -> None:
    sign_up(client)
    client.put("/api/me/schedule", json={"intervals": []})

    with TestClient(app) as other:
        sign_up(other, email="other@example.com", public_name="Other")
        assert other.get("/api/me/schedule").json() == {"intervals": WEEKDAYS_9_TO_5}

    assert client.get("/api/me/schedule").json() == {"intervals": []}


def test_schedule_needs_a_session(client: TestClient) -> None:
    assert client.get("/api/me/schedule").status_code == 401
    assert client.put("/api/me/schedule", json={"intervals": []}).status_code == 401
