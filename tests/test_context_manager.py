"""Tests for ContextManager business logic."""
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from contextualizer import storage
from contextualizer.models import Context, ContextSetting, ContextsFile, Settings
from contextualizer.context_manager import ContextManager


def _make_manager(contexts: list[Context], active_id: str | None = None) -> ContextManager:
    """Helper: build a ContextManager with given contexts loaded from a mock."""
    contexts_file = ContextsFile(contexts=contexts)
    settings = Settings(active_context_id=active_id)

    with (
        patch.object(storage, "load_contexts", return_value=contexts_file),
        patch.object(storage, "load_settings", return_value=settings),
        patch.object(storage, "save_settings"),
    ):
        return ContextManager()


def _dir(path: str) -> ContextSetting:
    return ContextSetting(key="dir", value=path, type="directory")


def test_get_all_contexts_empty():
    manager = _make_manager([])
    assert manager.get_all_contexts() == []


def test_get_active_context_none_when_no_active():
    ctx = Context(name="Work")
    manager = _make_manager([ctx], active_id=None)
    assert manager.get_active_context() is None


def test_get_active_context_returns_resolved():
    ctx = Context(name="Work", tags=["work"], settings=[_dir("/work")])
    manager = _make_manager([ctx], active_id=ctx.id)
    resolved = manager.get_active_context()
    assert resolved is not None
    assert resolved.name == "Work"
    assert resolved.tags == ["work"]
    assert resolved.breadcrumb == ["Work"]


def test_inheritance_tags_and_settings():
    parent = Context(name="Finance", tags=["finance"], settings=[_dir("/finance")])
    child = Context(
        name="Retirement",
        parent_id=parent.id,
        tags=["retirement"],
        settings=[_dir("/retirement")],
    )
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()

    assert resolved.tags == ["finance", "retirement"]
    assert resolved.settings == [_dir("/finance"), _dir("/retirement")]
    assert resolved.breadcrumb == ["Finance", "Retirement"]


def test_inheritance_deduplicates_tags():
    parent = Context(name="Finance", tags=["finance", "shared"])
    child = Context(name="Retirement", parent_id=parent.id, tags=["shared", "retirement"])
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()

    # "shared" appears once, in first-seen (parent) order
    assert resolved.tags == ["finance", "shared", "retirement"]


def test_inheritance_deduplicates_settings():
    parent = Context(name="Finance", settings=[_dir("/shared"), _dir("/finance")])
    child = Context(name="Retirement", parent_id=parent.id, settings=[_dir("/shared"), _dir("/retirement")])
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()

    # "/shared" appears once, in first-seen (parent) order
    assert resolved.settings == [_dir("/shared"), _dir("/finance"), _dir("/retirement")]


def test_settings_key_case_insensitive_dedup():
    parent = Context(name="Finance", settings=[ContextSetting(key="Dir", value="/finance", type="directory")])
    child = Context(name="Retirement", parent_id=parent.id, settings=[ContextSetting(key="dir", value="/finance", type="directory")])
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()

    # Same key (different case) + same value = one entry
    assert len(resolved.settings) == 1


def test_description_child_overrides_parent():
    parent = Context(name="Finance", description="General finance.")
    child = Context(name="Retirement", parent_id=parent.id, description="Retirement planning.")
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()
    assert resolved.description == "Retirement planning."


def test_description_inherited_from_parent():
    parent = Context(name="Finance", description="General finance.")
    child = Context(name="Retirement", parent_id=parent.id)
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()
    assert resolved.description == "General finance."


def test_description_none_when_no_parent_description():
    parent = Context(name="Finance")
    child = Context(name="Retirement", parent_id=parent.id)
    manager = _make_manager([parent, child], active_id=child.id)
    resolved = manager.get_active_context()
    assert resolved.description is None


def test_cycle_guard_does_not_hang():
    ctx = Context(name="Cycle")
    # Create a cycle by patching parent_id after creation
    ctx.parent_id = ctx.id
    manager = _make_manager([ctx], active_id=ctx.id)
    # Should return without hanging
    resolved = manager.get_active_context()
    assert resolved is not None
    assert resolved.breadcrumb == ["Cycle"]


def test_set_active_context_fires_callback():
    ctx = Context(name="Work")
    manager = _make_manager([ctx])

    called = threading.Event()
    manager.on_change(called.set)

    with patch.object(storage, "save_settings"):
        manager.set_active_context(ctx.id)

    assert called.wait(timeout=1.0)


def test_set_active_context_unknown_raises():
    manager = _make_manager([])
    with pytest.raises(ValueError, match="Unknown context id"):
        with patch.object(storage, "save_settings"):
            manager.set_active_context("nonexistent-id")


def test_set_active_context_none_clears():
    ctx = Context(name="Work")
    manager = _make_manager([ctx], active_id=ctx.id)
    with patch.object(storage, "save_settings"):
        manager.set_active_context(None)
    assert manager.get_active_context() is None


def test_relative_duration_expiry():
    ctx = Context(name="Work", duration="+1m")
    manager = _make_manager([ctx], active_id=ctx.id)

    # Patch _parse_expiry to return a timestamp in the past so _reschedule_expiry
    # detects delay <= 0 and calls set_active_context(None) immediately (no timer needed).
    past_ts = time.time() - 1.0
    with (
        patch.object(manager, "_parse_expiry", return_value=past_ts),
        patch.object(storage, "save_settings"),
    ):
        manager.set_active_context(ctx.id)

    assert manager.get_active_context() is None


def test_parse_relative_duration():
    ctx = Context(name="Work", duration="+2h")
    manager = _make_manager([ctx])
    now = time.time()
    expiry = manager._parse_expiry(ctx)
    assert expiry is not None
    assert abs(expiry - (now + 7200)) < 5


def test_parse_absolute_time_future():
    import datetime

    ctx = Context(name="Work", duration="23:59")
    manager = _make_manager([ctx])
    manager._settings.active_context_selected_at = time.time()

    expiry = manager._parse_expiry(ctx)
    assert expiry is not None
    # Should be today's 23:59 or tomorrow's 23:59
    assert expiry > time.time()


def test_forever_duration_no_expiry():
    ctx = Context(name="Work", duration="forever")
    manager = _make_manager([ctx])
    assert manager._parse_expiry(ctx) is None


def test_get_all_resolved():
    parent = Context(name="Finance", tags=["finance"])
    child = Context(name="Retirement", parent_id=parent.id, tags=["retirement"])
    manager = _make_manager([parent, child])
    all_resolved = manager.get_all_resolved()
    assert len(all_resolved) == 2
    names = {r.name for r in all_resolved}
    assert names == {"Finance", "Retirement"}
