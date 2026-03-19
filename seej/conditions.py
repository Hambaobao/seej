"""Condition parsing and evaluation for filtering examples."""

import ast
import operator
from typing import Any, Callable, Optional
from rich.console import Console

console = Console()


class SafeExampleProxy:
    """安全的样本代理，支持 ex['key'] 和 ex.key 两种语法"""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        """支持 ex['key'] 语法"""
        return self._data.get(key)

    def __getattr__(self, key):
        """支持 ex.key 语法"""
        if key.startswith("_"):
            raise AttributeError(f"Cannot access private attribute: {key}")
        return self._data.get(key)

    def __contains__(self, key):
        """支持 'key' in ex"""
        return key in self._data

    def get(self, key, default=None):
        """支持 ex.get('key', default)"""
        return self._data.get(key, default)


def create_safe_namespace():
    """创建安全的执行命名空间"""
    # 只允许安全的内置函数和操作符
    safe_builtins = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "any": any,
        "all": all,
        "isinstance": isinstance,
        "True": True,
        "False": False,
        "None": None,
    }
    return safe_builtins


def validate_condition_syntax(condition: str) -> tuple[bool, Optional[str]]:
    """
    验证条件表达式的语法安全性

    Returns:
        (is_valid, error_message)
    """
    # 检查是否包含 'ex'
    if "ex" not in condition:
        return False, "Condition must reference 'ex' (e.g., ex['field'] == 'value')"

    # 尝试解析 AST
    try:
        tree = ast.parse(condition, mode="eval")
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    # 检查危险操作
    dangerous_nodes = (
        ast.Import,
        ast.ImportFrom,  # 禁止导入
        ast.Call,  # 暂时禁止所有函数调用（可以放宽）
    )

    for node in ast.walk(tree):
        # 允许安全的函数调用
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in create_safe_namespace():
                    return False, f"Function '{func_name}' is not allowed"

        # 禁止其他危险操作
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "Import statements are not allowed"

    return True, None


def build_condition_function(conditions: list[str]) -> Optional[Callable]:
    """
    构建条件过滤函数

    Args:
        conditions: 条件表达式列表，例如 ["ex['type'] == 'chat'", "len(ex['messages']) > 5"]

    Returns:
        过滤函数或 None
    """
    if not conditions:
        return None

    console.print("[bold]Building filter conditions:[/bold]")

    # 验证并处理每个条件
    validated_conditions = []
    for idx, cond in enumerate(conditions, 1):
        cond = cond.strip()
        if not cond:
            continue

        is_valid, error = validate_condition_syntax(cond)
        if not is_valid:
            console.print(f"[red]✗[/red] Condition {idx}: {cond}")
            console.print(f"  [red]Error: {error}[/red]")
            continue

        validated_conditions.append(cond)
        console.print(f"[green]✓[/green] Condition {idx}: [cyan]{cond}[/cyan]")

    if not validated_conditions:
        console.print("[yellow]Warning: No valid conditions, showing all examples[/yellow]")
        return None

    # 组合所有条件
    combined_expr = " and ".join(f"({c})" for c in validated_conditions)
    console.print(f"\n[bold]Combined:[/bold] [dim]{combined_expr}[/dim]\n")

    # 编译表达式
    try:
        compiled_code = compile(combined_expr, "<condition>", "eval")
    except Exception as e:
        console.print(f"[red]Failed to compile conditions: {e}[/red]")
        return None

    # 创建安全的命名空间
    safe_namespace = create_safe_namespace()

    def condition_filter(example: dict) -> bool:
        """实际的过滤函数"""
        try:
            # 创建代理对象
            ex = SafeExampleProxy(example)
            # 在安全命名空间中执行
            namespace = {**safe_namespace, "ex": ex}
            result = eval(compiled_code, {"__builtins__": {}}, namespace)
            return bool(result)
        except KeyError as e:
            # 字段不存在时返回 False
            return False
        except Exception as e:
            # 其他错误：打印警告但不中断
            # console.print(f"[yellow]Warning: Condition evaluation error: {e}[/yellow]")
            return False

    try:
        console.print(f"\n[red][bold]>>>Press any key to see jsonl!<<<\n[/bold][/red]")
        input()
    except KeyboardInterrupt:
        console.print(f"\n[bold]Keyboard Interruptted[/bold]\n")
        exit(0)

    return condition_filter


# ============ 向后兼容的旧版解析（可选保留） ============
