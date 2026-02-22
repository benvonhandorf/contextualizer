## Overview

Contextualizer is a system tray app to allow you to set a work context and then consume that information within multiple other apps, often via plugins or extensions.

It is written in Python and uses the `pystray` library.  The system will work on Linux, Mac and Windows but Linux is the primary target OS.

### What is a Context?

A context is the thing you're working on.  If you're researching for a project, that is the context.  If you're working on your retirement investments, that is the context.

You have one active context at a time, but a context can have a parent context allowing you to inherit data from the parent.  For example, `Finance -> Retirement` lets you manage the data at multiple levels, getting more specific. Children are additive to the parent context, adding new tags, directories, etc.

The context can then define information that you can consume inside other apps via plugins and extensions.

For example:
- Tags: Tags set on the context would be added to any new or modified notes while the context is active.
- Working Directories: Directories that are relevant to the work you're doing can be accessed quickly via Contextualizer's icon.

## How does it work?

Contextualizer provides a simple interface for managing your contexts, which are serialized as a JSON file for easy portability (or hacking).  The current local settings (e.g. active context) is managed separately so you can sync your list of contexts without changing what is selected.

Contextualizer then provides a simple, local only webservice that plugins can call to determine information about the current context.  By default, this webservice is provided on port 18647.

### Plugins

Most users will just want to consume plugins for their various applications.  These are provided in separate repositories, but the first party plugins for Contextualizer are:

#### Obsidian: (needs repository)

Provides tagging support for notes created or edited within a specific context.

### API

The API is documented using OpenAPI in `docs/openapi`.  The API is a simple, read only interface to the current state of Contextualizer.

## Future

Contextualizer may eventually also provide a communication mechanism for plugins to each other, within a context.  This would allow a VS Code plugin to "publish" information about the work done into an obsidian note, logging the areas of code edited and when.
