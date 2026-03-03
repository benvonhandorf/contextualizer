"""Tests for the FastAPI HTTP endpoints."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from contextualizer.api import create_app
from contextualizer.models import Context, ContextSetting, ResolvedContext


def _make_resolved(ctx: Context, breadcrumb: list[str] | None = None) -> ResolvedContext:
    return ResolvedContext(
        id=ctx.id,
        name=ctx.name,
        parent_id=ctx.parent_id,
        tags=ctx.tags,
        settings=ctx.settings,
        description=ctx.description,
        duration=ctx.duration,
        breadcrumb=breadcrumb or [ctx.name],
    )


@pytest.fixture
def manager():
    return MagicMock()


@pytest.fixture
def client(manager):
    app = create_app(manager)
    return TestClient(app, raise_server_exceptions=True)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_context_no_active(client, manager):
    manager.get_active_context.return_value = None
    response = client.get("/context")
    assert response.status_code == 204


def test_context_active(client, manager):
    ctx = Context(
        name="Work",
        tags=["work"],
        settings=[ContextSetting(key="dir", value="/work", type="directory")],
    )
    resolved = _make_resolved(ctx)
    manager.get_active_context.return_value = resolved

    response = client.get("/context")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Work"
    assert data["tags"] == ["work"]
    assert data["settings"] == [{"key": "dir", "value": "/work", "type": "directory"}]
    assert data["breadcrumb"] == ["Work"]
    assert data["id"] == ctx.id


def test_context_with_parent(client, manager):
    child = Context(name="Retirement", tags=["finance", "retirement"])
    resolved = _make_resolved(child, breadcrumb=["Finance", "Retirement"])
    manager.get_active_context.return_value = resolved

    response = client.get("/context")
    assert response.status_code == 200
    data = response.json()
    assert data["breadcrumb"] == ["Finance", "Retirement"]
    assert data["tags"] == ["finance", "retirement"]


def test_contexts_empty(client, manager):
    manager.get_all_resolved.return_value = []
    response = client.get("/contexts")
    assert response.status_code == 200
    assert response.json() == []


def test_contexts_list(client, manager):
    ctx1 = Context(name="Finance")
    ctx2 = Context(name="Work")
    manager.get_all_resolved.return_value = [
        _make_resolved(ctx1),
        _make_resolved(ctx2),
    ]

    response = client.get("/contexts")
    assert response.status_code == 200
    names = {c["name"] for c in response.json()}
    assert names == {"Finance", "Work"}
