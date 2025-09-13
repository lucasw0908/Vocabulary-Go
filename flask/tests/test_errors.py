from flask import testing


def test_404_page(client: testing.FlaskClient):
    resp = client.get("/definitely-not-exist-404")
    assert resp.status_code == 404
    assert b"404" in resp.data or b"Not Found" in resp.data
