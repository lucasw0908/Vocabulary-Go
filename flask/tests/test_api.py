from flask import testing

from app.models.libraries import Libraries


def test_api_user_requires_login(client: testing.FlaskClient):
    client.get("/logout")  # Ensure no user is logged in
    resp = client.get("/api/user")
    assert resp.status_code == 401


def test_api_user_ok(logged_in_client: testing.FlaskClient):
    resp = logged_in_client.get("/api/user")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "username" in data
    assert "email" in data
    assert "is_admin" in data
    assert "library" in data


def test_change_user_library_valid(logged_in_client: testing.FlaskClient):
    lib = Libraries.query.first()
    assert lib is not None
    resp = logged_in_client.put(f"/api/change_user_library/{lib.name}")
    assert resp.status_code == 200


def test_toggle_favorite_and_favorites(logged_in_client: testing.FlaskClient):
    lib = Libraries.query.first()
    assert lib is not None
    resp = logged_in_client.put(f"/api/favorites/{lib.name}")
    assert resp.status_code == 200
    resp2 = logged_in_client.get("/api/favorites")
    assert resp2.status_code == 200
    data = resp2.get_json()
    assert "favorite_ids" in data
