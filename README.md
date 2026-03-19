# seej

**seej** 是一个交互式 JSONL 浏览器，具有丰富的渲染功能，用于查看 `.jsonl`（JSON Lines）文件。它为复杂数据结构提供可自定义的渲染选项，并支持插件系统以实现可扩展性。

## 功能特性

- **交互式浏览** - 使用键盘控制浏览 JSONL 文件
- **丰富渲染** - 使用 `rich` 库实现精美格式化
- **可自定义字段渲染** - 针对不同类型的数据（消息、表格、嵌套结构等）提供不同的渲染器
- **过滤功能** - 基于自定义 Python 表达式过滤条目
- **插件系统** - 用于自定义渲染器的可扩展架构
- **多种视图模式** - 在富文本和纯文本渲染之间切换

## 安装

```bash
# 暂未发布，pip 不可用
pip install seej

# 请先 clone 本仓库并手动安装
git clone http://this-repo-name
pip install cloned-folder/
```

## 快速开始

```bash
# 基本用法
seej path/to/file.jsonl

# 导航到特定索引
seej path/to/file.jsonl -I 10

# 禁用富文本格式化（纯文本模式）
seej path/to/file.jsonl --raw
```

## 自定义字段渲染

seej 支持对不同类型的数据字段使用自定义渲染器：

```bash
# 将特定字段渲染为聊天消息
seej data.jsonl -r messages=chat,conversation

# 使用不同的渲染器渲染字段
seej data.jsonl -r text=description -r messages=messages

# 列出所有可用的渲染器
seej --list-renderers
```

### 内置渲染器

- `messages` - 用于具有角色/内容结构的聊天/对话数据
- `text`（别名：`str`、`string`）- 用于文本和通用内容
- `eye` - 原始输出渲染器

## 数据过滤

使用 `--condition` 或 `-c` 标志，通过 Python 表达式过滤条目：

```bash
# 仅显示 type 为 "chat" 的条目
seej data.jsonl -c 'ex["type"] == "chat"'

# 显示消息数量超过 5 条的条目
seej data.jsonl -c 'len(ex["messages"]) > 5'

# 组合多个条件
seej data.jsonl -c 'ex["type"] == "chat"' -c 'len(ex["messages"]) > 3'
```

> **注意**：使用引号包裹过滤条件以避免 shell 解释！变量 `ex` 代表当前正在评估的 JSON 对象。

## 插件系统

seej 支持可以提供额外渲染器的插件。插件架构使用 Python 的入口点（entry points）机制。

### 安装插件

```bash
pip install seej-plugin-nested  # 示例插件
```

嵌套结构插件提供：
- `nested` - 自动检测并选择最佳渲染（字典使用树视图，列表使用表格）
- `nested_dict` / `nested_tree` - 嵌套字典的树视图
- `nested_list` / `nested_table` - 字典列表的表格视图
- `json` - 带语法高亮和行号的 JSON 格式
- `compact` - 单行紧凑表示

### 使用插件渲染器

```bash
# 使用插件中的嵌套渲染器
seej data.jsonl -r nested=config,metadata

# 对字典列表使用表格格式
seej data.jsonl -r nested_table=records
```

### 可用插件示例

`seej-plugin-nested` 为复杂嵌套结构提供增强渲染：

```bash
# 自动渲染嵌套字段
seej data.jsonl -r nested=config,metadata

# 强制对字典使用树视图
seej data.jsonl -r nested_tree=settings

# 强制对列表使用表格视图
seej data.jsonl -r nested_table=items
```

## 使用示例

```bash
# 基本用法 - 浏览 JSONL 文件
seej data.jsonl

# 从特定索引开始
seej data.jsonl -I 5

# 使用条件过滤条目
seej data.jsonl -c 'ex["status"] == "active"'

# 为特定字段自定义渲染
seej data.jsonl -r messages=conversation -r text=description

# 使用插件渲染器
seej data.jsonl -r nested=complex_data

# 禁用插件加载
seej data.jsonl --no-plugins

# 列出所有可用的渲染器（包括插件渲染器）
seej --list-renderers
```

## 键盘控制

浏览时：
- `下` 或 `右` - 下一条
- `上` 或 `左` - 上一条
- `Q` 或 `X` - 退出
- `T` - 在富文本和纯文本模式之间切换

## 插件开发

开发者可以创建自定义插件来扩展 seej 的功能。插件通过 Python 的入口点系统在 `seej.plugins` 组下被发现。

有关插件开发指南，请参阅 **seej-plugin-nested仓库 - 插件开发指南**。

## 许可证

MIT

## 联系方式

- Email: jason.yang98@foxmail.com