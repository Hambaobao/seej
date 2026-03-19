"""Default fallback renderer."""

from .base import register_renderer


@register_renderer(
    "eye",
    description="Raw",
)
@register_renderer(
    "text",
    description="Render text and generic content",
)
def eye(v, **kwargs):
    """默认渲染器：直接打印"""
    print(v)
