"""Plugin system for seej."""

from .loader import (
    discover_plugins,
    load_plugin,
    load_all_plugins,
)

__all__ = [
    "discover_plugins",
    "load_plugin",
    "load_all_plugins",
]
