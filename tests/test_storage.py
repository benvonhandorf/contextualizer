"""Tests for JSON file storage."""
from pathlib import Path
from unittest.mock import patch

from contextualizer.models import Context, ContextsFile, Settings
from contextualizer import storage


def _patch_paths(tmp_path: Path):
    """Context manager that redirects storage paths to a temp directory."""
    data_dir = tmp_path / "data"
    state_dir = tmp_path / "state"
    data_dir.mkdir()
    state_dir.mkdir()

    contexts_path = data_dir / "contexts.json"
    settings_path = state_dir / "settings.json"

    return (
        patch.object(storage, "_contexts_path", return_value=contexts_path),
        patch.object(storage, "_settings_path", return_value=settings_path),
    )


def test_load_contexts_missing_returns_empty(tmp_path):
    ctx_patch, set_patch = _patch_paths(tmp_path)
    with ctx_patch, set_patch:
        result = storage.load_contexts()
    assert result.contexts == []


def test_load_settings_missing_returns_defaults(tmp_path):
    ctx_patch, set_patch = _patch_paths(tmp_path)
    with ctx_patch, set_patch:
        result = storage.load_settings()
    assert result.active_context_id is None


def test_contexts_round_trip(tmp_path):
    ctx = Context(name="Work", tags=["work"], working_dirs=["/home/user/work"])
    data = ContextsFile(contexts=[ctx])

    ctx_patch, set_patch = _patch_paths(tmp_path)
    with ctx_patch, set_patch:
        storage.save_contexts(data)
        loaded = storage.load_contexts()

    assert len(loaded.contexts) == 1
    assert loaded.contexts[0].id == ctx.id
    assert loaded.contexts[0].name == "Work"
    assert loaded.contexts[0].tags == ["work"]


def test_settings_round_trip(tmp_path):
    settings = Settings(active_context_id="abc-123", active_context_selected_at=1234567890.0)

    ctx_patch, set_patch = _patch_paths(tmp_path)
    with ctx_patch, set_patch:
        storage.save_settings(settings)
        loaded = storage.load_settings()

    assert loaded.active_context_id == "abc-123"
    assert loaded.active_context_selected_at == 1234567890.0
