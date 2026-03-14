# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contextualizer is a system tray application that manages "work contexts" and exposes them to other apps via a local-only HTTP webservice (default port **18647**). Plugins and extensions in other apps query this service to get context-aware information (e.g. tags to apply to notes, relevant working directories).

### Core Concepts

- **Context**: The thing you're currently working on. Each context can have a parent context, forming a hierarchy (e.g. `Finance -> Retirement`) that allows data inheritance from parent to child.
- **Active context**: Only one context is active at a time.
- **Context data**: Each context stores `tags` (list of strings) and `settings` (key/value pairs with a type). Settings keys are case-insensitive; plugins and extensions assign meaning to specific keys (e.g. `dir` for a working directory).
- **Settings types**: `"directory"` (filesystem path) or `"string"` (arbitrary text).
- **Inheritance**: Child contexts inherit and extend their parent's tags and settings. Deduplication uses `(key.lower(), value)` so the same key can appear with different values.
- **Storage**: Contexts are serialized as a JSON file for portability. Active-context selection (and expiry time) is stored separately so context lists can be synced without losing local state.
- **API**: A read-only local HTTP webservice. Spec lives in [docs/openapi/openapi.yaml](docs/openapi/openapi.yaml).

## Architecture

The system has two main surfaces:

1. **System tray UI** — allows the user to view, switch, and manage contexts. Contexts with children are shown as nested submenus. The currently active context (and its ancestors) are indicated with check marks.
2. **Local HTTP API** — read-only endpoint that plugins/extensions call to get the current context state. Documented via OpenAPI in `docs/openapi/`.

Contexts form a tree structure; when resolving context data, child contexts inherit from their parent chain.

### Key modules (`src/contextualizer/`)

| Module | Responsibility |
|--------|---------------|
| `models.py` | Pydantic data models: `Context`, `ResolvedContext`, `ContextSetting` |
| `context_manager.py` | Thread-safe manager: CRUD, `set_active_context`, `_resolve` (inheritance), expiry scheduling, change notifications. All methods that need `_resolve` must hold `_lock`. |
| `api.py` | HTTP server (stdlib `http.server`) exposing `GET /context`, `GET /contexts`, etc. |
| `tray.py` | `pystray` system tray icon and nested menu. `checked=` values on `MenuItem` must be callables (`lambda _, v=val: v`), not raw booleans. |
| `storage.py` | JSON read/write for contexts and settings files. |
| `platform/` | OS-specific code. Each platform module exports `load_icon()` and `check_environment()`. `check_environment()` is called at startup and raises `RuntimeError` if the environment is unsuitable. |

### Logging

`context_manager.py` logs context changes at `INFO` level with the full breadcrumb path (e.g. `"Finance -> Retirement"`). `__main__.py` calls `logging.basicConfig` at startup.

## OS Dependencies

The system supports Linux, Mac and Windows.  Warn before using anything that does not work cross-platform.
Platform dependent code should be kept in separate files per operating system.

- **Linux**: `check_environment()` verifies `DISPLAY` or `WAYLAND_DISPLAY` is set.
- **macOS / Windows**: Not yet implemented; `check_environment()` raises immediately with a descriptive message.