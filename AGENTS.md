# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contextualizer is a system tray application that manages "work contexts" and exposes them to other apps via a local-only HTTP webservice (default port **18647**). Plugins and extensions in other apps query this service to get context-aware information (e.g. tags to apply to notes, relevant working directories).

### Core Concepts

- **Context**: The thing you're currently working on. Each context can have a parent context, forming a hierarchy (e.g. `Finance -> Retirement`) that allows data inheritance from parent to child.
- **Active context**: Only one context is active at a time.
- **Context data**: Each context stores attributes like tags and working directories that plugins consume.
- **Storage**: Contexts are serialized as a JSON file for portability.
- **API**: A read-only local HTTP webservice. Spec lives in [docs/openapi/openapi.yaml](docs/openapi/openapi.yaml).

## Architecture

The system has two main surfaces:

1. **System tray UI** — allows the user to view, create, switch, and manage contexts.
2. **Local HTTP API** — read-only endpoint that plugins/extensions call to get the current context state. Documented via OpenAPI in `docs/openapi/`.

Contexts form a tree structure; when resolving context data, child contexts inherit from their parent chain.

## OS Dependencies

The system supports Linux, Mac and Windows.  Warn before using anything that does not work cross-platform.
Platform dependent code should be kept in separate files per operating system.