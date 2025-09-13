from flask import testing


def test_index(client: testing.FlaskClient):
    resp = client.get("/")
    assert resp.status_code == 200


def test_library(logged_in_client: testing.FlaskClient):
    resp = logged_in_client.get("/library")
    assert resp.status_code == 200


def test_word_test(logged_in_client: testing.FlaskClient):
    resp = logged_in_client.get("/word_test", follow_redirects=True)
    assert resp.status_code == 200


def test_sentence_test(logged_in_client: testing.FlaskClient):
    resp = logged_in_client.get("/sentence_test", follow_redirects=True)
    assert resp.status_code == 200


def test_card(logged_in_client: testing.FlaskClient):
    resp = logged_in_client.get("/card", follow_redirects=True)
    assert resp.status_code == 200


def test_tos_pdf(client: testing.FlaskClient):
    resp = client.get("/tos")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type") == "application/pdf"


def test_social_redirects(client: testing.FlaskClient):
    for path in ["/github", "/discord", "/twitter", "/facebook", "/instagram"]:
        resp = client.get(path, follow_redirects=False)
        assert resp.status_code in (302, 303)
