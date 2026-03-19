"""Messages renderer for chat/conversation data."""

from typing import Union, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from .base import register_renderer, safe_wrapper

console = Console()


# ============ Content Processing ============


def parse_content_item(item: Dict[str, Any]) -> str:
    """
    解析单个 content item

    支持格式:
    - {"type": "text", "text": "..."}
    - {"type": "image", "image": "url/base64"}
    - {"type": "image_url", "image_url": {"url": "..."}}
    """
    item_type = item.get("type", None)

    if item_type is None:
        try_keys = ["text", "image", "image_url"]
        for k in try_keys:
            if k in item:
                item_type = k
                break

    if item_type is None:
        item_type = "unknown"

    if item_type == "text":
        return item.get("text", "") + "\n"

    elif item_type == "image":
        # 直接 image 字段
        image_data = item.get("image", "")
        return render_image_placeholder(image_data)

    elif item_type == "image_url":
        # OpenAI 格式: {"type": "image_url", "image_url": {"url": "..."}}
        image_url_obj = item.get("image_url", {})
        if isinstance(image_url_obj, dict):
            url = image_url_obj.get("url", "")
        else:
            url = str(image_url_obj)
        return render_image_placeholder(url)

    else:
        # 未知类型，尝试通用处理
        return f"[Unknown content type: {item_type}]"


def render_image_placeholder(image_data: str) -> str:
    """渲染图片占位符"""
    if not image_data:
        return "[🖼️  Image: (empty)]"

    # 判断是 URL 还是 base64
    if image_data.startswith(("http://", "https://")):
        # URL 格式，显示缩短的 URL
        if len(image_data) > 60:
            display_url = image_data[:57] + "..."
        else:
            display_url = image_data
        return f"[🖼️  Image URL: {display_url}]"

    elif image_data.startswith("data:image"):
        # Base64 格式
        # 提取图片类型 (e.g., data:image/png;base64,...)
        try:
            header = image_data.split(",")[0]
            img_format = header.split("/")[1].split(";")[0].upper()
        except:
            img_format = "Unknown"

        data_size = len(image_data)
        size_kb = data_size / 1024

        if size_kb < 1024:
            size_str = f"{size_kb:.1f}KB"
        else:
            size_str = f"{size_kb/1024:.1f}MB"

        return f"[🖼️  Image: {img_format}, ~{size_str}]"

    else:
        # 其他格式，显示长度
        return f"[🖼️  Image: {len(image_data)} chars]"


def normalize_content(content: Union[str, List, None]) -> str:
    """
    标准化 content 字段，支持新旧格式

    旧格式: "content": "string"
    新格式: "content": [{"type": "text", "text": "..."}, {"type": "image", ...}]
    """
    if content is None:
        return ""

    # 旧格式：直接是字符串
    if isinstance(content, str):
        return content

    # 新格式：List[Dict]
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(parse_content_item(item))
            else:
                # 容错：非字典元素
                parts.append(str(item))

        # 直接拼接，不加分隔符（符合规范）
        return "".join(parts)

    # 其他类型，尝试转字符串
    return str(content)


# ============ Tool Calls Rendering ============


def render_tool_calls(msgs_turn: Dict, show_tool_call_details: bool) -> str:
    """渲染工具调用"""
    content = ""
    if "tool_calls" not in msgs_turn:
        return content

    tool_calls = msgs_turn["tool_calls"]
    if not tool_calls:
        return content

    content = "\n" + "─" * 15 + "(From Seej)" + "─" * 15 + "\n"
    content += "Tool Calls:\n"

    for idx, tc in enumerate(tool_calls):
        func_name = tc.get("function", {}).get("name", "unknown")
        tc_id = tc.get("id", "unknown")
        content += f"[{idx}] {func_name} [id:{tc_id}]"

        if show_tool_call_details:
            arguments = tc.get("function", {}).get("arguments", "")
            # 格式化参数显示
            if arguments:
                # 如果参数很长，截断显示
                if len(arguments) > 100:
                    args_display = arguments[:97] + "..."
                else:
                    args_display = arguments
                content += f"\n      Args: {args_display}"

        content += "\n"

    return content


# ============ Extra Fields Rendering ============


def render_extra_fields(msgs_turn: Dict, exclude_fields: set = None) -> str:
    """渲染额外字段"""
    if exclude_fields is None:
        exclude_fields = {"content", "role", "tool_calls"}

    extra_fields = [k for k in msgs_turn if k not in exclude_fields]

    if not extra_fields:
        return ""

    content = "\n" + "─" * 15 + "(From Seej)" + "─" * 15 + "\n"
    content += "Extra Fields:\n"

    for extra_k in extra_fields:
        extra_v = msgs_turn[extra_k]
        extra_v_rep = str(extra_v)

        # 长字段截断
        if len(extra_v_rep) > 100:
            extra_v_rep = extra_v_rep[:97] + "..."

        content += f"[{extra_k}]: {extra_v_rep}\n"

    return content


# ============ Role Display ============


def format_role_label(turn_idx: int, role: str) -> str:
    """格式化角色标签"""
    role_emoji = {
        "user": "👤",
        "assistant": "🤖",
        "system": "⚙️",
        "tool": "🔧",
    }

    emoji = role_emoji.get(role.lower(), "💬")
    return f"{emoji} [{turn_idx}] {role.upper()}"


# ============ Main Renderers ============


def messages_process_norich(v: List[Dict], show_tool_call_details: bool, **kwargs):
    """无富文本模式渲染消息"""
    if not v:
        print("(Empty messages)")
        return

    for turn_idx, info in enumerate(v):
        role = info.get("role", "unknown")
        print(f"\n{'='*60}")
        print(format_role_label(turn_idx, role))
        print("=" * 60)

        # 处理 content（支持新旧格式）
        content = normalize_content(info.get("content"))
        if content:
            print(content)

        # 渲染工具调用
        if "tool_calls" in info:
            print(render_tool_calls(info, show_tool_call_details))

        # 渲染额外字段
        extra = render_extra_fields(info)
        if extra:
            print(extra)


@register_renderer(
    "messages",
    description="Render chat messages with role/content structure",
)
def messages_process(v: List[Dict], no_rich: bool = False, show_tool_call_details: bool = False, **kwargs):
    """
    渲染消息列表

    支持格式:
    1. 旧格式: [{"role": "user", "content": "text"}]
    2. 新格式: [{"role": "user", "content": [{"type": "text", "text": "..."}, {"type": "image", ...}]}]
    """
    if not v:
        console.print("[dim](Empty messages)[/dim]")
        return

    if no_rich:
        return messages_process_norich(v, show_tool_call_details, **kwargs)

    # Rich 模式
    table = Table(
        show_header=False,
        # padding=(0, 1),
        collapse_padding=False,
    )
    table.add_column("ROLE", style="bold cyan", width=20, vertical="top")
    table.add_column("CONTENT", overflow="fold")

    for turn_idx, info in enumerate(v):
        role = info.get("role", "unknown")
        role_label = format_role_label(turn_idx, role)

        # 处理 content（支持新旧格式）
        content = normalize_content(info.get("content"))

        # 添加工具调用
        if "tool_calls" in info:
            content += render_tool_calls(info, show_tool_call_details)

        # 添加额外字段
        content += render_extra_fields(info)
        content = content.rstrip("\n")

        table.add_row(role_label, safe_wrapper(content) if content else Text("(empty)", style="dim"), end_section=True)

    console.print(table, crop=False, justify="left")


# ============ Utility: Detect Format ============


def detect_message_format(messages: List[Dict]) -> str:
    """
    检测消息格式版本

    Returns:
        'legacy': 旧格式 (content is str)
        'new': 新格式 (content is list)
        'mixed': 混合格式
        'unknown': 无法判断
    """
    if not messages:
        return "unknown"

    formats = set()
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            formats.add("legacy")
        elif isinstance(content, list):
            formats.add("new")

    if len(formats) == 0:
        return "unknown"
    elif len(formats) == 1:
        return formats.pop()
    else:
        return "mixed"
