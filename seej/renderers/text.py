"""Text and generic renderers."""

from rich.console import Console
from .base import register_renderer, safe_wrapper

console = Console()


def renderable_norich(v):
    """无富文本模式"""
    print(v)


@register_renderer("text", aliases=["str", "string"], description="Render text and generic content")
def renderable(v, no_rich=False, **kwargs):
    """渲染通用可显示内容"""
    try:
        if no_rich:
            return renderable_norich(v)

        if isinstance(v, dict):
            from .default import eye  # 避免循环导入

            for sub_k, sub_v in v.items():
                print(f"< Key = {sub_k} >")
                renderer = kwargs.get("_mapper", {}).get(sub_k, eye)
                renderer(sub_v, **kwargs)
                print()
        elif isinstance(v, list):
            from .default import eye

            for sub_v in v:
                eye(sub_v, no_rich=no_rich, **kwargs)
                print()
        else:
            console.print(safe_wrapper(v))
    except Exception:
        from .default import eye

        return eye(v, **kwargs)
