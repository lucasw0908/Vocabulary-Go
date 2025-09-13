from flask import testing

from app.settings import SYSTEM_EMAIL, SYSTEM_PASSWORD


def test_login_page(client: testing.FlaskClient):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_success(client: testing.FlaskClient):
    resp = client.post(
        "/login",
        data={"email": SYSTEM_EMAIL, "password": SYSTEM_PASSWORD, "remember": "on"},
        follow_redirects=True,
    )
    assert resp.status_code == 200


def test_login_fail(client: testing.FlaskClient):
    resp = client.post(
        "/login",
        data={"email": "not-exist@example.com", "password": "wrong"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_logout(logged_in_client: testing.FlaskClient):
    resp = logged_in_client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("Location", "").endswith("/login")
