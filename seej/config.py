"""Configuration parsing for seej."""

from typing import Dict, Callable
from rich.console import Console
from rich.table import Table
from .renderers.base import get_renderer, list_renderers, get_all_renderer_names

console = Console()


def parse_render_mappings(render_args) -> Dict[str, Callable]:
    """解析渲染映射参数"""
    field_mapper = {}
    if not render_args:
        return field_mapper

    for mapping in render_args:
        if "=" not in mapping:
            console.print(f"[yellow]Warning: Invalid mapping format '{mapping}', expected 'renderer=field1,field2'[/yellow]")
            continue

        renderer_name, fields_str = mapping.split("=", 1)
        renderer = get_renderer(renderer_name.strip())

        if renderer is None:
            console.print(f"[yellow]Warning: Unknown renderer '{renderer_name}'[/yellow]")

            # 尝试给出建议
            all_names = get_all_renderer_names()
            suggestions = [name for name in all_names if renderer_name.lower() in name.lower()]
            if suggestions:
                console.print(f"[dim]Did you mean: {', '.join(suggestions[:3])}?[/dim]")
            console.print(f"[dim]Use --list-renderers to see all available options[/dim]")
            continue

        for field in fields_str.split(","):
            field = field.strip()
            if field:
                field_mapper[field] = renderer
                console.print(f"[green]✓[/green] Mapped '{field}' → {renderer_name}")

    return field_mapper


def print_available_renderers():
    """打印所有可用的渲染器"""
    renderers = list_renderers()

    if not renderers:
        console.print("[yellow]No renderers available[/yellow]")
        return

    table = Table(title="Available Renderers", show_header=True, header_style="bold magenta")
    table.add_column("Renderer", style="cyan", no_wrap=True)
    table.add_column("Source", style="yellow", width=12)
    table.add_column("Aliases", style="dim")
    table.add_column("Description", style="green")

    # 按来源分组排序
    builtin_renderers = []
    plugin_renderers = []

    for name, info in renderers.items():
        if info.source == "builtin":
            builtin_renderers.append((name, info))
        else:
            plugin_renderers.append((name, info))

    # 先显示内置，再显示插件
    for name, info in sorted(builtin_renderers) + sorted(plugin_renderers):
        source = info.source
        if info.plugin_name:
            source = f"📦 {info.plugin_name}"

        aliases = ", ".join(info.aliases) if info.aliases else "-"
        desc = info.description or "-"

        table.add_row(name, source, aliases, desc)

    console.print(table)
    console.print("\n[bold]Usage:[/bold] seej data.jsonl -r [cyan]<renderer>[/cyan]=[green]<field1>[/green],[green]<field2>[/green]...")
    console.print("[bold]Example:[/bold] seej data.jsonl -r messages=chat,conversation")
