import threading

import uvicorn

from contextualizer.api import create_app
from contextualizer.context_manager import ContextManager
from contextualizer.tray import TrayApp

# Default port. Plugins must be configured with the same value if changed.
_DEFAULT_PORT = 18647


def _run_server(manager: ContextManager) -> None:
    """Run the uvicorn HTTP server. Intended to run in a daemon thread."""
    app = create_app(manager)
    config = uvicorn.Config(
        app,
        host="127.0.0.1",  # local-only — never expose on 0.0.0.0
        port=_DEFAULT_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    server.run()


def main() -> None:
    manager = ContextManager()

    # HTTP API server runs in a daemon thread; it exits automatically when the
    # main thread (tray) exits.
    server_thread = threading.Thread(target=_run_server, args=(manager,), daemon=True)
    server_thread.start()

    # pystray requires the tray event loop to run on the main thread.
    TrayApp(manager).run()


if __name__ == "__main__":
    main()
