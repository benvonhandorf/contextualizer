from __future__ import annotations

from typing import Callable, Optional

import pystray

from contextualizer import platform as ctx_platform
from contextualizer.context_manager import ContextManager
from contextualizer.models import Context


def _build_context_items(
    by_parent: dict[Optional[str], list[Context]],
    parent_id: Optional[str],
    make_switch: Callable[[str], Callable],
    active_ancestors: set[str],
    active_id: Optional[str],
) -> list[pystray.MenuItem]:
    """Recursively build menu items for contexts at the given parent level."""
    items = []
    for ctx in sorted(by_parent.get(parent_id, []), key=lambda c: c.name):
        action = make_switch(ctx.id)
        # pystray requires checked to be a callable, not a raw bool.
        is_active = ctx.id == active_id
        if ctx.id in by_parent:
            # Has children: submenu with a "Select" entry at the top.
            # Mark the submenu header as checked if this context or any descendant is active.
            in_ancestors = ctx.id in active_ancestors
            sub_items: list = [
                pystray.MenuItem(f"Select {ctx.name}", action, checked=lambda _, v=is_active: v, radio=True),
                pystray.Menu.SEPARATOR,
            ]
            sub_items.extend(
                _build_context_items(by_parent, ctx.id, make_switch, active_ancestors, active_id)
            )
            items.append(
                pystray.MenuItem(
                    ctx.name,
                    pystray.Menu(*sub_items),
                    checked=lambda _, v=in_ancestors: v,
                )
            )
        else:
            items.append(pystray.MenuItem(ctx.name, action, checked=lambda _, v=is_active: v, radio=True))
    return items


def _build_menu(manager: ContextManager) -> pystray.Menu:
    """Construct the tray drop-down menu from current context state."""
    items: list[pystray.MenuItem] = []

    active = manager.get_active_context()
    active_label = active.breadcrumb_str() if active else "No Context"

    items.append(pystray.MenuItem(f"Context: {active_label}", None, enabled=False))
    items.append(pystray.Menu.SEPARATOR)

    # Factory function captures ctx_id by value, avoiding the loop-variable bug.
    def make_switch(ctx_id: str) -> Callable:
        def switch(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
            manager.set_active_context(ctx_id)
        return switch

    # Group contexts by parent_id for tree traversal.
    all_contexts = manager.get_all_contexts()
    by_id: dict[str, Context] = {c.id: c for c in all_contexts}
    by_parent: dict[Optional[str], list[Context]] = {}
    for ctx in all_contexts:
        by_parent.setdefault(ctx.parent_id, []).append(ctx)

    # Collect the IDs on the path from root down to the active context so that
    # submenu headers can be marked as checked when a descendant is active.
    active_id = active.id if active else None
    active_ancestors: set[str] = set()
    cursor = by_id.get(active_id) if active_id else None
    while cursor is not None:
        active_ancestors.add(cursor.id)
        cursor = by_id.get(cursor.parent_id) if cursor.parent_id else None

    items.extend(_build_context_items(by_parent, None, make_switch, active_ancestors, active_id))

    items.append(pystray.Menu.SEPARATOR)

    def clear(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        manager.set_active_context(None)

    no_context_checked = active_id is None
    items.append(pystray.MenuItem("No Context", clear, checked=lambda _, v=no_context_checked: v, radio=True))
    items.append(pystray.Menu.SEPARATOR)

    def quit_app(icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        icon.stop()

    items.append(pystray.MenuItem("Quit", quit_app))

    return pystray.Menu(*items)


class TrayApp:
    def __init__(self, manager: ContextManager) -> None:
        self._manager = manager
        self._icon: Optional[pystray.Icon] = None

    def _rebuild_menu(self) -> None:
        """Called by ContextManager change callbacks (may run from any thread)."""
        if self._icon is None:
            return
        active = self._manager.get_active_context()
        self._icon.title = active.breadcrumb_str() if active else "Contextualizer"
        self._icon.menu = _build_menu(self._manager)

    def run(self) -> None:
        """
        Blocking call — runs the pystray event loop on the calling thread.
        Must be called from the main thread.
        """
        image = ctx_platform.load_icon()
        active = self._manager.get_active_context()
        title = active.breadcrumb_str() if active else "Contextualizer"

        self._icon = pystray.Icon(
            name="contextualizer",
            icon=image,
            title=title,
            menu=_build_menu(self._manager),
        )

        self._manager.on_change(self._rebuild_menu)
        self._icon.run()
