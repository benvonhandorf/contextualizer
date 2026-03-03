from fastapi import FastAPI, Response

from contextualizer.context_manager import ContextManager
from contextualizer.models import ResolvedContext


def create_app(manager: ContextManager) -> FastAPI:
    """
    Factory that creates the FastAPI application.
    Accepts a ContextManager instance so the app is testable in isolation.
    """
    app = FastAPI(
        title="Contextualizer",
        description="Read-only local HTTP API for the current work context state.",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/context")
    def get_active_context(response: Response) -> ResolvedContext | None:
        """
        Returns the currently active context with all inherited data resolved.
        Returns 204 if no context is active.
        """
        ctx = manager.get_active_context()
        if ctx is None:
            response.status_code = 204
            return None
        return ctx

    @app.get("/contexts", response_model=list[ResolvedContext])
    def get_all_contexts() -> list[ResolvedContext]:
        """Returns all defined contexts with resolved inherited data."""
        return manager.get_all_resolved()

    return app
