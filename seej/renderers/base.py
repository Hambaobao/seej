"""Renderer registry and base utilities."""

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.text import Text

console = Console()


@dataclass
class RendererInfo:
    """渲染器信息"""

    name: str  # 主名称
    function: Callable  # 渲染函数
    aliases: List[str]  # 别名列表
    description: str  # 描述
    source: str = "builtin"  # 来源: builtin, plugin
    plugin_name: Optional[str] = None  # 插件名称


# 全局渲染器注册表
_RENDERER_REGISTRY: Dict[str, RendererInfo] = {}


def register_renderer(name: str, aliases: list = None, description: str = "", source: str = "builtin", plugin_name: Optional[str] = None):
    """
    装饰器：注册渲染器

    Args:
        name: 渲染器主名称
        aliases: 别名列表
        description: 描述信息
        source: 来源 (builtin/plugin)
        plugin_name: 插件名称（如果是插件提供）
    """

    def decorator(func: Callable):
        aliases_list = aliases or []

        renderer_info = RendererInfo(name=name, function=func, aliases=aliases_list, description=description, source=source, plugin_name=plugin_name)

        # 注册主名称
        _RENDERER_REGISTRY[name] = renderer_info

        # 注册所有别名
        for alias in aliases_list:
            _RENDERER_REGISTRY[alias] = renderer_info

        return func

    return decorator


def register_plugin_renderers(renderers: Dict[str, Callable], plugin_name: str, descriptions: Dict[str, str] = None) -> int:
    """
    批量注册插件提供的渲染器

    Args:
        renderers: {name: function} 字典
        plugin_name: 插件名称
        descriptions: {name: description} 字典

    Returns:
        注册的渲染器数量
    """
    descriptions = descriptions or {}
    count = 0

    for name, func in renderers.items():
        # 检查是否已注册
        if name in _RENDERER_REGISTRY:
            existing = _RENDERER_REGISTRY[name]
            console.print(f"[yellow]Warning:[/yellow] Renderer '{name}' from plugin '{plugin_name}' " f"overrides existing renderer from '{existing.source}'")

        # 注册渲染器
        renderer_info = RendererInfo(name=name, function=func, aliases=[], description=descriptions.get(name, ""), source="plugin", plugin_name=plugin_name)  # 插件可以在 get_renderers() 中返回元数据

        _RENDERER_REGISTRY[name] = renderer_info
        count += 1

    return count


def get_renderer(name: str) -> Optional[Callable]:
    """获取渲染器函数"""
    info = _RENDERER_REGISTRY.get(name)
    return info.function if info is not None else None


def get_renderer_info(name: str) -> Optional[RendererInfo]:
    """获取渲染器完整信息"""
    return _RENDERER_REGISTRY.get(name)


def list_renderers() -> Dict[str, RendererInfo]:
    """列出所有注册的渲染器"""
    # 去重：相同函数只返回主名称
    seen_functions = {}
    result = {}

    for name, info in _RENDERER_REGISTRY.items():
        func_id = id(info.function)

        if func_id not in seen_functions:
            # 第一次遇到这个函数，记录为主名称
            seen_functions[func_id] = name
            result[name] = info
        else:
            # 已经见过，将当前名称作为别名添加
            main_name = seen_functions[func_id]
            if name != main_name and name not in result[main_name].aliases:
                result[main_name].aliases.append(name)

    return result


def get_all_renderer_names() -> List[str]:
    """获取所有渲染器名称（包括别名）"""
    return list(_RENDERER_REGISTRY.keys())


def safe_wrapper(v):
    """安全包装文本"""
    if v is None:
        return Text()
    return Text(str(v), overflow="fold")
