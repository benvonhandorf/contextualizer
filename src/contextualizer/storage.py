from pathlib import Path

from platformdirs import user_data_dir, user_state_dir

from contextualizer.models import ContextsFile, Settings


def _contexts_path() -> Path:
    return Path(user_data_dir("contextualizer", ensure_exists=True)) / "contexts.json"


def _settings_path() -> Path:
    return Path(user_state_dir("contextualizer", ensure_exists=True)) / "settings.json"


def load_contexts() -> ContextsFile:
    """Load contexts.json; returns empty ContextsFile if missing."""
    p = _contexts_path()
    if not p.exists():
        return ContextsFile()
    return ContextsFile.model_validate_json(p.read_text())


def save_contexts(data: ContextsFile) -> None:
    _contexts_path().write_text(data.model_dump_json(indent=2))


def load_settings() -> Settings:
    """Load settings.json; returns default Settings if missing."""
    p = _settings_path()
    if not p.exists():
        return Settings()
    return Settings.model_validate_json(p.read_text())


def save_settings(settings: Settings) -> None:
    _settings_path().write_text(settings.model_dump_json(indent=2))
