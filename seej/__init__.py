"""seej - Interactive JSONL browser with rich rendering."""

__version__ = "0.2.0"

from .see_jsonl import main
from .renderers import register_renderer, get_renderer
from .conditions import SafeExampleProxy, build_condition_function

__all__ = [
    "main",
    "register_renderer",
    "get_renderer",
    "SafeExampleProxy",
    "build_condition_function",
]
