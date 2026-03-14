## Overview

Contextualizer is a system tray app to allow you to set a work context and then consume that information within multiple other apps, often via plugins or extensions.

It is written in Python and uses the `pystray` library.  The system will work on Linux, Mac and Windows but Linux is the primary target OS.

### Installation

Contextualizer is a python package.  Install it's dependencies using your favorite `pyproject.toml` tool (e.g. `uv`).

### What is a Context?

A context is the thing you're working on.  If you're researching for a project, that is the context.  If you're working on your retirement investments, that is the context.

You have one active context at a time, but a context can have a parent context allowing you to inherit data from the parent.  For example, `Finance -> Retirement` lets you manage the data at multiple levels, getting more specific. Children are additive to the parent context, adding new tags, directories, etc.

The context can then define information that you can consume inside other apps via plugins and extensions.  All information is optional.

For example:
- Tags: Tags set on the context would be added to any new or modified notes while the context is active.
- Context Settings
    - Settings have a key and a type.
    - Keys are strings with no particular assumptions as to contents.  Keys are **not** case sensitive.
    - Extensions and plugins may assign specific meanings to different keys.
    - Setting Types
        - Directory: A filesystem directory.  Should be created before the context is activated.
        - String: Text string
- Description: A free-text field describing the content.  Can be used for LLM instructions about work done in this context.
- Duration: A description of how long to keep the current context active.  Once this is reached, Contextualizer returns to having no selected context.
    - `forever`: Default, keep this context active until another context is selected.
    - time, e.g. `5:00 PM` or `1700`: Keep this context active until the specified time (today, or tomorrow if this time is already in the past today).  
    - duration, e.g. `+2h`: Keep the context active for the specified duration from when it was last selected.

### Picking a Context

To select an existing context, simply click on the Contextualizer icon and then pick your context from the menu.  Contexts are shown in a nested menu that mirrors the parent/child hierarchy, so selecting a child context is done through its parent's submenu.  The currently active context is indicated with a check mark.

You can also tell contextualizer to clear the current context by selecting `No Context` from the menu.

For now, contexts are defined by editing the `json` file directly.  A UI will eventually be provided.

## How does it work?

Contextualizer provides a simple interface for managing your contexts, which are serialized as a JSON file for easy portability (or hacking).  The current local settings (e.g. active context) is managed separately so you can sync your list of contexts without changing what is selected.

Contextualizer then provides a simple, local only webservice that plugins can call to determine information about the current context.  By default, this webservice is provided on port 18647 (which can be configured, but must also be configured in the plugins).

### Application Plugins / Extensions

Most users will just want to consume plugins for their various applications.  These are provided in separate repositories, but the first party plugins for Contextualizer are:

#### Obsidian: (needs repository)

Provides tagging support for notes created or edited within a specific context.

### API

The API is documented using OpenAPI in `docs/openapi`.  The API is a simple, read only interface to the current state of Contextualizer.

## Future

### History

Allow plugins to publish a list or changes they've made, such as "Moved <filename> to <directory>".

### Communication

Contextualizer may eventually also provide a communication mechanism for plugins to each other, within a context.  This would allow a VS Code plugin to "publish" information about the work done into an obsidian note, logging the areas of code edited and when.

