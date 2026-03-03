"""Tests for data model serialization and defaults."""
import uuid

from contextualizer.models import Context, ContextSetting, ContextsFile, ResolvedContext, Settings


def test_context_defaults():
    ctx = Context(name="Work")
    assert ctx.duration == "forever"
    assert ctx.tags == []
    assert ctx.settings == []
    assert ctx.parent_id is None
    assert ctx.description is None
    # id is a valid UUID
    uuid.UUID(ctx.id)


def test_context_json_round_trip():
    ctx = Context(
        name="Finance",
        tags=["finance"],
        settings=[ContextSetting(key="dir", value="/home/user/finance", type="directory")],
    )
    data = ContextsFile(contexts=[ctx])
    reloaded = ContextsFile.model_validate_json(data.model_dump_json())
    assert reloaded.contexts[0].id == ctx.id
    assert reloaded.contexts[0].tags == ["finance"]
    assert reloaded.contexts[0].settings == ctx.settings


def test_settings_defaults():
    s = Settings()
    assert s.active_context_id is None
    assert s.active_context_selected_at is None


def test_resolved_context_breadcrumb_str():
    rc = ResolvedContext(
        id="x",
        name="Retirement",
        tags=[],
        settings=[],
        duration="forever",
        breadcrumb=["Finance", "Retirement"],
    )
    assert rc.breadcrumb_str() == "Finance -> Retirement"


def test_resolved_context_single_breadcrumb():
    rc = ResolvedContext(
        id="x",
        name="Work",
        tags=[],
        settings=[],
        duration="forever",
        breadcrumb=["Work"],
    )
    assert rc.breadcrumb_str() == "Work"
