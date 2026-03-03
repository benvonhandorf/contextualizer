from __future__ import annotations

from typing import Optional

import pystray

from contextualizer import platform as ctx_platform
from contextualizer.context_manager import ContextManager


def _build_menu(manager: ContextManager) -> pystray.Menu:
    """Construct the tray drop-down menu from current context state."""
    items: list[pystray.MenuItem] = []

    active = manager.get_active_context()
    active_label = active.breadcrumb_str() if active else "No Context"

    items.append(pystray.MenuItem(f"Context: {active_label}", None, enabled=False))
    items.append(pystray.Menu.SEPARATOR)

    for ctx in sorted(manager.get_all_contexts(), key=lambda c: c.name):
        # Factory function captures ctx_id by value, avoiding the loop-variable bug.
        def make_switch(ctx_id: str):
            def switch(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
                manager.set_active_context(ctx_id)

            return switch

        items.append(pystray.MenuItem(ctx.name, make_switch(ctx.id)))

    items.append(pystray.Menu.SEPARATOR)

    def clear(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        manager.set_active_context(None)

    items.append(pystray.MenuItem("No Context", clear))
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
