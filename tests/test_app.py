import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn and play chess",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["existing@school.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_catalog(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@school.edu"]


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new@school.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Signed up new@school.edu for Chess Club"
    assert "new@school.edu" in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "existing@school.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "existing@school.edu"
    ]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "new@school.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "existing@school.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered existing@school.edu from Chess Club"
    assert client.get("/activities").json()["Chess Club"]["participants"] == []


def test_unregister_rejects_missing_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "missing@school.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "existing@school.edu"
    ]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/participants",
        params={"email": "existing@school.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"