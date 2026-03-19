"""Renderers module - auto-import all renderers."""

from .base import (
    register_renderer,
    register_plugin_renderers,
    get_renderer,
    get_renderer_info,
    list_renderers,
    get_all_renderer_names,
    safe_wrapper,
    console,
)
from .default import eye
from .messages import messages_process
from .text import renderable

# 不再需要手动维护 default_mapper
# 所有渲染器都通过注册表管理

__all__ = [
    "register_renderer",
    "register_plugin_renderers",
    "get_renderer",
    "get_renderer_info",
    "list_renderers",
    "get_all_renderer_names",
    "eye",
    "console",
    "safe_wrapper",
]
