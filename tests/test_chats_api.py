"""Chat routes: the shapes the frontend reads, owner isolation, and input limits."""

import pytest
from fastapi.testclient import TestClient

from aria.app import create_app
from aria.auth.caller import Caller, current_caller


@pytest.fixture
def app(settings):
    return create_app(settings, preflight_on_startup=False, catalog_on_startup=False)


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


def as_user(app, user_id):
    app.dependency_overrides[current_caller] = lambda: Caller(user_id=user_id)


def test_chat_lifecycle_uses_the_frontend_shapes(client):
    created = client.post("/api/chats", json={"title": "New Chat"}).json()

    assert set(created) == {"id", "title", "createdAt", "updatedAt", "messageCount", "isNew"}
    assert created["isNew"] is True
    assert client.get("/api/chats").json() == [
        {key: created[key] for key in ("id", "title", "createdAt", "updatedAt")}
    ]

    chat_id = created["id"]
    details = client.get(f"/api/chats/{chat_id}").json()
    assert details["messages"] == []
    assert "userId" not in details

    renamed = client.put(f"/api/chats/{chat_id}", json={"title": "Leave questions"}).json()
    assert renamed["title"] == "Leave questions"
    assert client.post(f"/api/chats/{chat_id}/metrics", json={"clientDurationMs": 1200}).json() == {
        "status": "recorded",
        "id": chat_id,
    }
    assert client.delete(f"/api/chats/{chat_id}").json() == {"status": "deleted"}
    assert client.get(f"/api/chats/{chat_id}").status_code == 404


def test_gateway_prefixed_paths_reach_the_same_chats(client):
    created = client.post("/api/gateway/api/chats", json={}).json()

    assert created["title"] == "New Chat"
    assert client.get("/api/gateway/chats").json()[0]["id"] == created["id"]


def test_another_users_chat_looks_like_a_missing_one(app, client):
    as_user(app, "owner")
    chat_id = client.post("/api/chats", json={"title": "Private"}).json()["id"]

    as_user(app, "someone-else")
    assert client.get("/api/chats").json() == []
    for response in (
        client.get(f"/api/chats/{chat_id}"),
        client.put(f"/api/chats/{chat_id}", json={"title": "Taken"}),
        client.delete(f"/api/chats/{chat_id}"),
        client.post(f"/api/chats/{chat_id}/metrics", json={}),
    ):
        assert response.status_code == 404
        assert response.json() == {"detail": "Chat not found"}

    as_user(app, "owner")
    assert client.get(f"/api/chats/{chat_id}").json()["title"] == "Private"


def test_titles_are_cleaned_and_bounded(client):
    long_title = "A" * 100
    created = client.post("/api/chats", json={"title": f"  line\nbreak\x00 {long_title}"}).json()

    assert "\n" not in created["title"] and "\x00" not in created["title"]
    assert len(created["title"]) == 40
    assert created["title"].endswith("...")


def test_chats_per_owner_are_capped(settings):
    settings.deployment.chats.max_chats_per_owner = 2
    app = create_app(settings, preflight_on_startup=False, catalog_on_startup=False)
    with TestClient(app) as client:
        assert client.post("/api/chats", json={}).status_code == 200
        assert client.post("/api/chats", json={}).status_code == 200
        assert client.post("/api/chats", json={}).status_code == 429


def test_chat_ids_must_be_numbers(client):
    assert client.get("/api/chats/not-a-number").status_code == 422
