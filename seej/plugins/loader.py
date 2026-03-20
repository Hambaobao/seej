"""Plugin discovery and loading system."""

import sys

from typing import List
from importlib import metadata
from rich.console import Console

console = Console()

# 插件入口点组名
PLUGIN_ENTRY_POINT_GROUP = "seej.plugins"


class PluginInfo:
    """插件信息"""

    def __init__(self, name: str, version: str, entry_point):
        self.name = name
        self.version = version
        self.entry_point = entry_point
        self.loaded = False
        self.renderer_count = 0
        self.error = None


def discover_plugins() -> List[PluginInfo]:
    """发现所有已安装的 seej 插件"""
    plugins = []

    # Python 3.10+ 使用新 API
    if sys.version_info >= (3, 10):
        entry_points = metadata.entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
    else:
        # Python 3.7-3.9 兼容
        eps = metadata.entry_points()
        entry_points = eps.get(PLUGIN_ENTRY_POINT_GROUP, [])

    for entry_point in entry_points:
        try:
            dist = entry_point.dist
            version = dist.version if dist else "unknown"

            plugin_info = PluginInfo(name=entry_point.name, version=version, entry_point=entry_point)
            plugins.append(plugin_info)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to discover plugin {entry_point.name}: {e}[/yellow]")

    return plugins


def load_plugin(plugin_info: PluginInfo) -> int:
    """
    加载单个插件并注册渲染器

    Returns:
        注册的渲染器数量
    """
    from ..renderers.base import register_plugin_renderers

    try:
        # 加载入口点
        plugin_module = plugin_info.entry_point.load()

        # 获取渲染器
        if callable(plugin_module):
            # 如果是函数，调用获取渲染器
            result = plugin_module()
        else:
            # 如果是模块，查找 get_renderers 函数
            result = getattr(plugin_module, "get_renderers", lambda: {})()

        # 支持两种返回格式
        if isinstance(result, dict):
            # 简单格式: {name: function}
            renderers = result
            descriptions = {}
        elif isinstance(result, tuple) and len(result) == 2:
            # 扩展格式: ({name: function}, {name: description})
            renderers, descriptions = result
        else:
            raise TypeError(f"Plugin must return dict or (dict, dict), got {type(result)}")

        # 批量注册
        count = register_plugin_renderers(renderers, plugin_name=plugin_info.name, descriptions=descriptions)

        plugin_info.loaded = True
        plugin_info.renderer_count = count

        return count

    except Exception as e:
        plugin_info.error = str(e)
        console.print(f"[red]✗[/red] Failed to load plugin '{plugin_info.name}': {e}")
        return 0


def load_all_plugins(verbose: bool = True) -> int:
    """
    加载所有已安装的插件

    Returns:
        成功加载的渲染器总数
    """
    plugins = discover_plugins()
    total_renderers = 0

    if not plugins:
        if verbose:
            console.print("[dim]No plugins installed[/dim]")
        return 0

    if verbose:
        console.print(f"[bold]Loading {len(plugins)} plugin(s)...[/bold]")

    for plugin_info in plugins:
        count = load_plugin(plugin_info)
        total_renderers += count

        if plugin_info.loaded and verbose:
            console.print(f"[green]✓[/green] {plugin_info.name} "
                          f"[dim]v{plugin_info.version}[/dim] "
                          f"→ {count} renderer(s)")

    if verbose and total_renderers > 0:
        console.print()

    return total_renderers


def get_loaded_plugins() -> List[PluginInfo]:
    """获取所有已加载的插件信息"""
    plugins = discover_plugins()
    for plugin_info in plugins:
        load_plugin(plugin_info)
    return plugins
