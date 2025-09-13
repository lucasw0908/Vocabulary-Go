from flask import Response, testing


def test_register_and_login_flow(client: testing.FlaskClient):
    # Register
    resp = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "pw12345",
            "confirm": "pw12345",
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)

    # Login with new user
    resp2: Response = client.post(
        "/login",
        data={"email": "new@example.com", "password": "pw12345", "remember": "on"},
        follow_redirects=False,
    )
    assert resp2.status_code in (302, 303)
    assert resp2.headers["Location"].endswith("/")
    
    logout_resp = client.get("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200


def test_settings_password_change(client: testing.FlaskClient):
    # Create and login a temporary user for password change tests
    client.post(
        "/register",
        data={
            "username": "changepw",
            "email": "changepw@example.com",
            "password": "oldpw",
            "confirm": "oldpw",
        },
        follow_redirects=False,
    )
    client.post(
        "/login",
        data={"email": "changepw@example.com", "password": "oldpw", "remember": "on"},
        follow_redirects=False,
    )

    # change password with wrong current
    resp = client.post(
        "/settings",
        data={
            "submit": "password",
            "current_password": "wrong",
            "new_password": "abc123",
            "confirm_password": "abc123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # change password with correct current
    resp2 = client.post(
        "/settings",
        data={
            "submit": "password",
            "current_password": "oldpw",
            "new_password": "newpw",
            "confirm_password": "newpw",
        },
        follow_redirects=True,
    )
    assert resp2.status_code == 200


