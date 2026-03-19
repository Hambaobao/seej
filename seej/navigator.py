"""Example navigator for browsing JSONL data."""

import os
from pathlib import Path
import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .tools import get_terminal_width, load_jsonl_iter
from .renderers.base import get_renderer
from .renderers import console

console = Console()


def control_str(s, wrap=False, raw=False):
    """打印控制信息"""

    if raw:
        console.print(s)
        return

    content = Text(s, style="bold red", overflow="fold")
    if wrap:
        content = Panel(content, expand=False, title="Control")
    console.print(content)


class ExampleNavigator:
    """JSONL 示例浏览器"""

    def __init__(
        self,
        file_path,
        start_idx=0,
        no_rich=False,
        condition_fn=None,
        condition_display=None,
        show_tool_call_details=False,
        custom_mapper=None,
    ):
        self.file_path = file_path
        self.start_idx = start_idx
        self.no_rich = no_rich
        self.condition_fn = condition_fn
        self.condition_display = condition_display or "None"
        self.custom_mapper = custom_mapper or {}

        self._render_configs = {
            "show_tool_call_details": show_tool_call_details,
        }

        self.current_idx = -1
        self.iterator = load_jsonl_iter(file_path, skip=start_idx)
        self.example_history = []

        self.navigate_next()
        self.run()

    def run(self):
        """主循环"""
        while True:
            try:
                key = readchar.readkey()
                if key == readchar.key.UP or key == readchar.key.LEFT:
                    self.navigate_previous()
                elif key == readchar.key.DOWN or key == readchar.key.RIGHT or key == readchar.key.ENTER:
                    self.navigate_next()
                elif key.casefold() in ["q", "x"]:
                    control_str("Quit.")
                    break
                elif key.casefold() == "t":
                    self.toggle_render_mode()
            except KeyboardInterrupt:
                control_str("Quit.")
                break
            except Exception as e:
                raise e

    def toggle_render_mode(self):
        """切换渲染模式"""
        self.no_rich = not self.no_rich
        self.display_current_example()
        control_str(f"Rendering mode toggled to {'raw' if self.no_rich else 'rich'}.")

    def navigate_previous(self):
        """导航到上一个示例"""
        if self.current_idx > 0:
            self.current_idx -= 1
            self.display_current_example()
        else:
            control_str("Cannot go back further.")

    def navigate_next(self):
        """导航到下一个示例"""

        def _progress_bar():
            primes = [7, 137, 313, 449, 601, 853, 1117]
            progress_str = ["."] * len(primes)

            def next(idx):
                nonlocal progress_str
                residual = idx % (primes[-1] + 500)
                if residual in primes:
                    progress_str = ["."] * len(primes)
                    progress_str[primes.index(residual)] = "#"
                return "".join(progress_str)

            return next

        if self.current_idx < len(self.example_history) - 1:
            self.current_idx += 1
        else:
            try:
                num_searched = 0
                progress_generator = _progress_bar()

                while True:
                    num_searched += 1

                    s = f"\r[{num_searched:6d}] Searching {progress_generator(num_searched)}"
                    print(s, end="", flush=True)

                    new_example = next(self.iterator)

                    # 应用过滤条件
                    if self.condition_fn is None or self.condition_fn(new_example):
                        break

                self.current_idx += 1
                self.example_history.append((self.current_idx + self.start_idx, new_example))
            except StopIteration:
                control_str("\nEnd of examples.")
                exit(0)

        self.display_current_example()

    def get_renderer_for_field(self, field_name):
        """获取字段的渲染器"""
        # 优先使用自定义映射
        if field_name in self.custom_mapper:
            ret = self.custom_mapper[field_name]
            return ret

        # 然后查找全局注册的渲染器
        renderer = get_renderer(field_name)
        if renderer is not None:
            return renderer

        # 最后使用默认渲染器
        return get_renderer("eye")

    def display_current_example(self):
        """显示当前示例"""
        os.system("clear")
        file_idx, ex = self.example_history[self.current_idx]
        largest_idx, _ = self.example_history[-1]

        for k, v in ex.items():
            renderer = self.get_renderer_for_field(k)
            s = f"[[red][bold]{k}[/bold][/red] [dim]@{renderer.__name__}[/dim]]"
            control_str(s, raw=True)

            renderer(
                v,
                no_rich=self.no_rich,
                **self._render_configs,
            )
            print("-" * get_terminal_width())

        s = f"IDX={file_idx} | LOADED=[{self.start_idx}, {largest_idx}]\n\n"
        s += "Prev(LEFT)  Next(RIGHT)  (Q)uit  (T)oggle"
        control_str(s, wrap=False)
        control_str(f"\nFilter: {self.condition_display}", wrap=False)
