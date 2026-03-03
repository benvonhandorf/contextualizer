from __future__ import annotations

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ContextSetting(BaseModel):
    """A key-value setting attached to a context."""
    key: str
    value: str
    type: Literal["directory", "string"]


class Context(BaseModel):
    """A single named work context."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    parent_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    settings: list[ContextSetting] = Field(default_factory=list)
    description: Optional[str] = None
    # Raw string: "forever", "5:00 PM", "1700", "+2h", "+30m"
    duration: str = "forever"


class ContextsFile(BaseModel):
    """Root structure of contexts.json."""

    contexts: list[Context] = Field(default_factory=list)


class Settings(BaseModel):
    """Root structure of settings.json — local state, not synced."""

    active_context_id: Optional[str] = None
    # Unix timestamp of when the active context was last selected; used for +duration math.
    active_context_selected_at: Optional[float] = None


class ResolvedContext(BaseModel):
    """A context with all inherited fields merged from the parent chain."""

    id: str
    name: str
    parent_id: Optional[str] = None
    # Merged root-to-leaf, deduplicated preserving first occurrence.
    tags: list[str]
    settings: list[ContextSetting]
    # Nearest ancestor (or self) description wins; child overrides parent.
    description: Optional[str] = None
    duration: str
    # Names from root ancestor to this context, e.g. ["Finance", "Retirement"].
    breadcrumb: list[str]

    def breadcrumb_str(self) -> str:
        return " -> ".join(self.breadcrumb)
