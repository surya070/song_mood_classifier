import sys
import os
import pytest
from app import app as flask_app

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client
