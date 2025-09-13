import os
import tempfile

import pytest
from flask import Flask, testing

from app import create_app
from app.config import Config
from app.settings import SYSTEM_EMAIL, SYSTEM_PASSWORD


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test_db.sqlite3")


@pytest.fixture(scope="session")
def app() -> Flask:
    
    app = create_app(TestConfig)
    app.app_context().push()
    
    return app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


@pytest.fixture
def logged_in_client(client: testing.FlaskClient):
    resp = client.post(
        "/login",
        data={"email": SYSTEM_EMAIL, "password": SYSTEM_PASSWORD, "remember": "on"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    return client
