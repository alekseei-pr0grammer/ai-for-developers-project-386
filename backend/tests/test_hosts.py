from datetime import UTC, datetime

from fastapi.testclient import TestClient


def sign_up(client: TestClient, **overrides: str):
    payload = {
        "email": "alex@example.com",
        "password": "correct horse battery",
        "public_name": "Alex Alekseev",
        "time_zone": "Europe/London",
    } | overrides
    return client.post("/api/auth/signup", json=payload)


def test_sign_up_creates_host_and_starts_session(client: TestClient) -> None:
    response = sign_up(client)

    assert response.status_code == 201
    assert response.json() == {
        "email": "alex@example.com",
        "public_name": "Alex Alekseev",
        "handle": "alex-alekseev",
        "time_zone": "Europe/London",
    }
    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["handle"] == "alex-alekseev"


def test_handle_gets_smallest_free_suffix_when_public_name_is_taken(client: TestClient) -> None:
    sign_up(client, email="a@example.com")
    sign_up(client, email="b@example.com")
    third = sign_up(client, email="c@example.com")

    assert third.json()["handle"] == "alex-alekseev-3"


def test_handle_is_transliterated_to_ascii(client: TestClient) -> None:
    response = sign_up(client, public_name="Алексей Алексеев")

    assert response.json()["handle"] == "aleksey-alekseev"


def test_handle_never_uses_a_reserved_app_path(client: TestClient) -> None:
    response = sign_up(client, public_name="Login")

    assert response.json()["handle"] == "login-2"


def test_sign_up_with_registered_email_in_any_case_is_a_conflict(client: TestClient) -> None:
    sign_up(client)

    response = sign_up(client, email="ALEX@Example.com")

    assert response.status_code == 409


def test_sign_up_rejects_unknown_time_zone_and_short_password(client: TestClient) -> None:
    assert sign_up(client, time_zone="Mars/Olympus").status_code == 422
    assert sign_up(client, password="short").status_code == 422


def test_logged_out_visitor_is_not_a_host(client: TestClient) -> None:
    assert client.get("/api/me").status_code == 401


def test_log_out_ends_the_session(client: TestClient) -> None:
    sign_up(client)

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/me").status_code == 401


def test_log_in_with_email_and_password(client: TestClient) -> None:
    sign_up(client)
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login", json={"email": "Alex@example.com", "password": "correct horse battery"}
    )

    assert response.status_code == 200
    assert response.json()["handle"] == "alex-alekseev"
    assert client.get("/api/me").status_code == 200


def test_log_in_failure_does_not_say_which_field_was_wrong(client: TestClient) -> None:
    sign_up(client)
    client.post("/api/auth/logout")

    wrong_password = client.post(
        "/api/auth/login", json={"email": "alex@example.com", "password": "wrong password"}
    )
    unknown_email = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "wrong password"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert client.get("/api/me").status_code == 401


def test_session_cookie_is_http_only(client: TestClient) -> None:
    response = sign_up(client)

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_session_expires(client: TestClient, set_now) -> None:
    set_now(datetime(2026, 1, 1, tzinfo=UTC))
    sign_up(client)

    set_now(datetime(2026, 3, 1, tzinfo=UTC))

    assert client.get("/api/me").status_code == 401


def test_host_changes_public_name_and_time_zone_but_keeps_handle(client: TestClient) -> None:
    sign_up(client)

    response = client.patch(
        "/api/me", json={"public_name": "Acme Support", "time_zone": "Asia/Tokyo"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "email": "alex@example.com",
        "public_name": "Acme Support",
        "handle": "alex-alekseev",
        "time_zone": "Asia/Tokyo",
    }
    assert client.get("/api/me").json()["public_name"] == "Acme Support"


def test_host_cannot_change_handle(client: TestClient) -> None:
    sign_up(client)

    response = client.patch("/api/me", json={"handle": "someone-else"})

    assert response.status_code == 422
    assert client.get("/api/me").json()["handle"] == "alex-alekseev"


def test_profile_update_is_validated(client: TestClient) -> None:
    sign_up(client)

    assert client.patch("/api/me", json={"public_name": "  "}).status_code == 422
    assert client.patch("/api/me", json={"time_zone": "Nowhere/Land"}).status_code == 422


def test_profile_update_needs_a_session(client: TestClient) -> None:
    assert client.patch("/api/me", json={"public_name": "X"}).status_code == 401
