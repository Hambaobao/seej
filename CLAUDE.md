# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**seej** is an interactive terminal-based JSONL (JSON Lines) browser written in Python. It lets users navigate `.jsonl` files record-by-record with rich rendering via the `rich` library. The project uses a plugin architecture for custom renderers.

This repository is a monorepo containing two separate packages (each with its own `.git`):
- `seej/` — the core CLI application
- `seej-plugin-nested/` — a plugin providing renderers for nested data structures

## Build & Install

```bash
# Install the core package (editable mode for development)
pip install -e seej/

# Install the plugin (optional)
pip install -e seej-plugin-nested/
```

Both packages use `setuptools` with `pyproject.toml`. The core package also uses `setuptools_scm` for version management.

## Running

```bash
seej data.jsonl                              # Basic usage
seej data.jsonl -I 10                        # Start at index 10
seej data.jsonl -R                           # Raw text mode (no rich)
seej data.jsonl -r messages=chat             # Map field to renderer
seej data.jsonl -c 'ex["type"] == "chat"'    # Filter with expression
seej --list-renderers                        # List available renderers
seej data.jsonl --no-plugins                 # Disable plugin loading
```

## Testing & Formatting

```bash
# No automated test suite exists yet. Dev dependencies include:
pip install -e "seej/[dev]"    # installs pytest and black

# Manual plugin test
python seej-plugin-nested/tests/test_renderer_nested.py

# Code formatting
black seej/ seej-plugin-nested/
```

## Architecture

### Entry Point & Navigation

`seej/seej/see_jsonl.py:main()` is the CLI entry point (registered as `seej` console script). It parses arguments, loads plugins, builds renderer mappings and filter conditions, then launches `ExampleNavigator`.

`seej/seej/navigator.py:ExampleNavigator` is the core interactive browser. It uses a keyboard event loop (`readchar`) for navigation and dispatches field rendering to registered renderers. JSONL records are loaded lazily via an iterator with a history buffer for backward navigation.

### Renderer System

The renderer registry lives in `seej/seej/renderers/base.py`. It uses a global `_RENDERER_REGISTRY` dict mapping names to `RendererInfo` dataclasses.

**Renderer resolution order** for each field (in `ExampleNavigator.get_renderer_for_field`):
1. Custom CLI mapping (`-r` flag)
2. Global registry lookup by field name
3. Fallback to the `eye` renderer (raw print)

Built-in renderers (in `seej/seej/renderers/`) register via the `@register_renderer` decorator. All renderer functions must accept `(v, no_rich=False, **kwargs)` and print output directly (no return value).

### Plugin System

Plugins are discovered via Python entry points under the `"seej.plugins"` group (`seej/seej/plugins/loader.py`). A plugin must expose a `get_renderers()` function returning either:
- `{name: function}` — simple format
- `({name: function}, {name: description})` — extended format with descriptions

Plugin registration in `pyproject.toml`:
```toml
[project.entry-points."seej.plugins"]
plugin_name = "package_name:get_renderers"
```

See `seej-plugin-nested/how-to-make-new-plugin.md` for a comprehensive plugin development guide (in Chinese).

### Condition/Filter System

`seej/seej/conditions.py` provides safe expression-based filtering. User expressions (via `-c`) are validated through AST analysis, compiled with restricted builtins, and evaluated against a `SafeExampleProxy` wrapper that sandboxes dict access. The variable `ex` refers to the current JSONL record in filter expressions.

## Key Conventions

- Code comments and docstrings are written in Chinese
- Documentation (READMEs, guides) is in Chinese
- Python >=3.7 compatibility is maintained (includes fallbacks for `importlib.metadata` API differences)
- The `rich` library is used throughout for terminal rendering
