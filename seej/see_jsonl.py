"""Main entry point for seej - JSONL browser."""

import argparse
from pathlib import Path

from .navigator import ExampleNavigator
from .config import parse_render_mappings, print_available_renderers
from .conditions import build_condition_function
from .plugins.loader import load_all_plugins
from .renderers.base import get_renderer
from .renderers import console


def build_effective_mapper(load_plugins: bool = True, custom_mappings: list = None):
    """
    构建有效的渲染器映射

    Args:
        load_plugins: 是否加载插件
        custom_mappings: 自定义映射列表

    Returns:
        {field_name: renderer_function} 映射字典
    """
    # 加载插件（会自动注册到全局注册表）
    if load_plugins:
        load_all_plugins(verbose=True)

    # 解析自定义映射
    custom_field_mapper = parse_render_mappings(custom_mappings)

    return custom_field_mapper


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Interactive JSONL browser with customizable renderers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  seej data.jsonl
  
  # Custom field rendering
  seej data.jsonl -r messages=chat,conversation
  
  # Using plugin renderers
  seej data.jsonl -r nested=config,metadata
  
  # Filter examples (wrap in quotes!)
  seej data.jsonl -c 'ex["type"] == "chat"'
  seej data.jsonl -c 'len(ex["messages"]) > 5'
  
  # List available renderers (including plugins)
  seej --list-renderers
  
  # Disable plugins
  seej data.jsonl --no-plugins

Note: Use quotes around filter conditions to avoid shell interpretation!
        """,
    )

    parser.add_argument("file", type=str, nargs="?", help="JSONL file to browse")
    parser.add_argument("-I", "--idx", type=int, default=0, help="Start from the given index")
    parser.add_argument("-R", "--raw", action="store_true", default=False, help="Use raw string output instead of rich rendering")
    parser.add_argument("-c", "--condition", type=str, nargs="+", dest="conditions", metavar="EXPR", help="Filter conditions using 'ex' variable (e.g., 'ex[\"type\"] == \"chat\"')")
    parser.add_argument("-r", "--render", action="append", metavar="RENDERER=FIELD[,FIELD...]", help="Map fields to renderers (e.g., messages=chat,convo)")
    parser.add_argument("--show-tool-call-details", default=False, action="store_true", help="Show detailed tool call information in messages")
    parser.add_argument("--list-renderers", action="store_true", help="List all available renderers and exit")
    parser.add_argument("--no-plugins", action="store_true", help="Disable plugin loading")

    args = parser.parse_args()

    # 列出渲染器（需要先加载插件）
    if args.list_renderers:
        if not args.no_plugins:
            load_all_plugins(verbose=False)
        print_available_renderers()
        return

    # 验证文件参数
    if not args.file:
        parser.error("the following arguments are required: file")

    if not Path(args.file).exists():
        console.print(f"[red]Error:[/red] File '{args.file}' does not exist.")
        return

    # 构建渲染器映射
    custom_field_mapper = build_effective_mapper(load_plugins=not args.no_plugins, custom_mappings=args.render)

    if args.render:
        console.print()

    # 构建过滤条件
    condition_fn = build_condition_function(args.conditions)
    condition_display = " AND ".join(args.conditions) if args.conditions else "None"

    # 启动导航器
    navigator = ExampleNavigator(
        args.file,
        start_idx=args.idx,
        no_rich=args.raw,
        condition_fn=condition_fn,
        condition_display=condition_display,
        show_tool_call_details=args.show_tool_call_details,
        custom_mapper=custom_field_mapper,
    )


if __name__ == "__main__":
    main()
