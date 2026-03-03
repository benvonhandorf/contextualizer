from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from dateutil import parser as dateutil_parser

from contextualizer import storage
from contextualizer.models import Context, ContextSetting, ResolvedContext, Settings


class ContextManager:
    """
    Central state manager. Thread-safe for reads; writes are serialized via a lock.
    Runs a background timer thread for duration-based context expiry.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._contexts: dict[str, Context] = {}
        self._settings: Settings = Settings()
        self._on_change_callbacks: list[Callable[[], None]] = []
        self._expiry_timer: Optional[threading.Timer] = None
        self.reload()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def reload(self) -> None:
        """Re-read both JSON files from disk. Safe to call at any time."""
        with self._lock:
            data = storage.load_contexts()
            self._contexts = {c.id: c for c in data.contexts}
            self._settings = storage.load_settings()
        self._reschedule_expiry()

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_all_contexts(self) -> list[Context]:
        with self._lock:
            return list(self._contexts.values())

    def get_active_context(self) -> Optional[ResolvedContext]:
        with self._lock:
            ctx_id = self._settings.active_context_id
            if ctx_id is None or ctx_id not in self._contexts:
                return None
            return self._resolve(self._contexts[ctx_id])

    def get_all_resolved(self) -> list[ResolvedContext]:
        with self._lock:
            return [self._resolve(c) for c in self._contexts.values()]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def set_active_context(self, context_id: Optional[str]) -> None:
        """Set or clear the active context. Pass None to clear."""
        with self._lock:
            if context_id is not None and context_id not in self._contexts:
                raise ValueError(f"Unknown context id: {context_id}")
            self._settings.active_context_id = context_id
            self._settings.active_context_selected_at = time.time() if context_id else None
            storage.save_settings(self._settings)
        self._reschedule_expiry()
        self._notify_change()

    # ------------------------------------------------------------------
    # Change notification
    # ------------------------------------------------------------------

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback to be invoked when the active context changes."""
        self._on_change_callbacks.append(callback)

    def _notify_change(self) -> None:
        for cb in self._on_change_callbacks:
            try:
                cb()
            except Exception:
                pass  # never let a callback crash the manager

    # ------------------------------------------------------------------
    # Duration / expiry timer
    # ------------------------------------------------------------------

    def _parse_expiry(self, ctx: Context) -> Optional[float]:
        """
        Returns a Unix timestamp for when this context should expire,
        or None if it never expires.
        """
        duration_str = ctx.duration.strip()
        if not duration_str or duration_str == "forever":
            return None

        selected_at = self._settings.active_context_selected_at or time.time()

        if duration_str.startswith("+"):
            return self._parse_relative(duration_str[1:], selected_at)

        return self._parse_absolute_time(duration_str)

    def _parse_relative(self, s: str, base: float) -> Optional[float]:
        """Parse '2h', '30m', '1h30m' into a future Unix timestamp."""
        total_seconds = 0
        for match in re.finditer(r"(\d+)([hm])", s.lower()):
            value, unit = int(match.group(1)), match.group(2)
            total_seconds += value * 3600 if unit == "h" else value * 60
        return (base + total_seconds) if total_seconds > 0 else None

    def _parse_absolute_time(self, s: str) -> Optional[float]:
        """
        Parse '5:00 PM', '1700', '17:00' into a Unix timestamp.
        If the resulting time is in the past today, use tomorrow.
        """
        try:
            # Normalize bare 4-digit time '1700' -> '17:00'
            if s.isdigit() and len(s) == 4:
                s = f"{s[:2]}:{s[2:]}"
            default_base = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            target = dateutil_parser.parse(s, default=default_base)
            if target <= datetime.now():
                target += timedelta(days=1)
            return target.timestamp()
        except Exception:
            return None

    def _reschedule_expiry(self) -> None:
        """Cancel any existing timer and schedule a new one if needed."""
        if self._expiry_timer is not None:
            self._expiry_timer.cancel()
            self._expiry_timer = None

        with self._lock:
            ctx_id = self._settings.active_context_id
            if ctx_id is None or ctx_id not in self._contexts:
                return
            expiry_ts = self._parse_expiry(self._contexts[ctx_id])

        if expiry_ts is None:
            return

        delay = expiry_ts - time.time()
        if delay <= 0:
            # Already expired; clear immediately (must not hold the lock here)
            self.set_active_context(None)
            return

        self._expiry_timer = threading.Timer(delay, self._on_expiry)
        self._expiry_timer.daemon = True
        self._expiry_timer.start()

    def _on_expiry(self) -> None:
        self.set_active_context(None)

    # ------------------------------------------------------------------
    # Inheritance resolution (must be called while holding _lock)
    # ------------------------------------------------------------------

    def _resolve(self, ctx: Context) -> ResolvedContext:
        """
        Walk the parent chain and produce a fully resolved context.

        Tags and settings are merged additively (root -> leaf), deduped.
        Description: the nearest ancestor with one wins; child overrides parent.
        Cycles are detected by tracking visited IDs.
        """
        chain: list[Context] = []
        visited: set[str] = set()
        current: Optional[Context] = ctx

        while current is not None:
            if current.id in visited:
                break  # cycle guard
            visited.add(current.id)
            chain.append(current)
            current = self._contexts.get(current.parent_id) if current.parent_id else None

        # Reverse so iteration goes root -> leaf
        chain.reverse()

        tags: list[str] = []
        seen_tags: set[str] = set()
        settings: list[ContextSetting] = []
        seen_settings: set[tuple[str, str]] = set()
        description: Optional[str] = None
        breadcrumb: list[str] = [c.name for c in chain]

        for c in chain:
            for tag in c.tags:
                if tag not in seen_tags:
                    seen_tags.add(tag)
                    tags.append(tag)
            for s in c.settings:
                key = (s.key.lower(), s.value)
                if key not in seen_settings:
                    seen_settings.add(key)
                    settings.append(s)
            if c.description is not None:
                description = c.description  # child overrides parent

        return ResolvedContext(
            id=ctx.id,
            name=ctx.name,
            parent_id=ctx.parent_id,
            tags=tags,
            settings=settings,
            description=description,
            duration=ctx.duration,
            breadcrumb=breadcrumb,
        )
