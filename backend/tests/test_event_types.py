from fastapi.testclient import TestClient

from app.main import app
from tests.api import create_event_type, sign_up


def test_host_creates_and_lists_event_types(client: TestClient) -> None:
    sign_up(client)

    created = create_event_type(client, title="Intro call", duration_minutes=15)
    create_event_type(client, title="Consultation", duration_minutes=60)

    assert created == {
        "id": created["id"],
        "title": "Intro call",
        "description": "A quick first chat.",
        "duration_minutes": 15,
        "archived": False,
    }
    listed = client.get("/api/me/event-types").json()
    assert [(e["title"], e["duration_minutes"]) for e in listed] == [
        ("Intro call", 15),
        ("Consultation", 60),
    ]


def test_host_edits_an_event_type(client: TestClient) -> None:
    sign_up(client)
    event_type = create_event_type(client)

    response = client.patch(
        f"/api/me/event-types/{event_type['id']}",
        json={"title": "Deep dive", "description": "", "duration_minutes": 90},
    )

    assert response.status_code == 200
    assert response.json() | {"id": 0} == {
        "id": 0,
        "title": "Deep dive",
        "description": "",
        "duration_minutes": 90,
        "archived": False,
    }


def test_event_type_needs_a_title_and_a_positive_duration(client: TestClient) -> None:
    sign_up(client)

    bad_title = client.post(
        "/api/me/event-types", json={"title": " ", "description": "", "duration_minutes": 30}
    )
    bad_duration = client.post(
        "/api/me/event-types", json={"title": "Call", "description": "", "duration_minutes": 0}
    )

    assert bad_title.status_code == bad_duration.status_code == 422


def test_host_cannot_touch_another_hosts_event_types(client: TestClient) -> None:
    sign_up(client)
    event_type = create_event_type(client)

    with TestClient(app) as other:
        sign_up(other, email="other@example.com", public_name="Other")
        response = other.patch(f"/api/me/event-types/{event_type['id']}", json={"title": "Mine"})
        listed = other.get("/api/me/event-types").json()

    assert response.status_code == 404
    assert listed == []


def test_event_types_need_a_session(client: TestClient) -> None:
    assert client.get("/api/me/event-types").status_code == 401


def test_guest_sees_host_public_name_and_active_event_types(client: TestClient) -> None:
    sign_up(client)
    create_event_type(client, title="Intro call")
    archived = create_event_type(client, title="Old offer")
    client.patch(f"/api/me/event-types/{archived['id']}", json={"archived": True})

    with TestClient(app) as guest:
        response = guest.get("/api/hosts/alex-alekseev")

    assert response.status_code == 200
    body = response.json()
    assert (body["public_name"], body["handle"]) == ("Alex Alekseev", "alex-alekseev")
    assert [e["title"] for e in body["event_types"]] == ["Intro call"]
    # The Host still sees the archived one.
    assert len(client.get("/api/me/event-types").json()) == 2


def test_unknown_handle_is_not_found(client: TestClient) -> None:
    assert client.get("/api/hosts/nobody").status_code == 404
