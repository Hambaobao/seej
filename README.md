# seej

**seej** is an interactive terminal JSONL (JSON Lines) browser with rich rendering. It helps you step through `.jsonl` files record by record, with pluggable renderers for complex data.

## Features

- **Interactive navigation** — keyboard-driven browsing through JSONL records
- **Rich output** — formatting via the `rich` library
- **Per-field renderers** — map fields to renderers (messages, tables, nested structures, etc.)
- **Filtering** — keep rows that match a safe Python expression
- **Plugins** — extend rendering via Python entry points
- **View modes** — switch between rich and plain-text rendering

## Installation

```bash
pip install seej
```

From a git checkout:

```bash
git clone https://github.com/<owner>/seej.git
cd seej
pip install .
```

## Quick start

```bash
# Basic usage
seej path/to/file.jsonl

# Start at a given record index
seej path/to/file.jsonl -I 10

# Plain text instead of rich rendering
seej path/to/file.jsonl --raw
```

(`-R` is a short alias for `--raw`.)

## Custom field renderers

Map JSON fields to named renderers:

```bash
# Render specific fields as chat-style messages
seej data.jsonl -r messages=chat,conversation

# Multiple mappings
seej data.jsonl -r text=description -r messages=messages

# List registered renderers
seej --list-renderers
```

### Built-in renderers

- `messages` — chat / role–content style payloads
- `text` (aliases: `str`, `string`) — general text
- `eye` — minimal / raw-style dump

## Filtering

Use `-c` / `--condition` with an expression evaluated per record (variable `ex` is the current object):

```bash
seej data.jsonl -c 'ex["type"] == "chat"'
seej data.jsonl -c 'len(ex["messages"]) > 5'
seej data.jsonl -c 'ex["type"] == "chat"' -c 'len(ex["messages"]) > 3'
```

Quote expressions so your shell does not rewrite them.

## Plugins

Plugins register extra renderers under the `seej.plugins` entry-point group.

### Example: nested structures

```bash
pip install seej-plugin-nested
```

That plugin adds renderers such as:

- `nested` — pick a reasonable view (tree for dicts, table for lists)
- `nested_dict` / `nested_tree` — tree views
- `nested_list` / `nested_table` — tabular views
- `json` — highlighted JSON with line numbers
- `compact` — single-line compact form

Usage:

```bash
seej data.jsonl -r nested=config,metadata
seej data.jsonl -r nested_table=records
seej data.jsonl -r nested_tree=settings
seej data.jsonl -r nested_table=items
```

## More examples

```bash
seej data.jsonl
seej data.jsonl -I 5
seej data.jsonl -c 'ex["status"] == "active"'
seej data.jsonl -r messages=conversation -r text=description
seej data.jsonl -r nested=complex_data
seej data.jsonl --no-plugins
seej --list-renderers
```

## Keyboard shortcuts

While browsing:

- **Down** or **Right** — next record
- **Up** or **Left** — previous record
- **Q** or **X** — quit
- **T** — toggle rich vs raw rendering

## Writing plugins

Plugins expose renderers through entry points. For a full walkthrough (including a guide in Chinese), see the **seej-plugin-nested** repository and its plugin documentation.

## License

MIT

## Contact

- Email: jason.yang98@foxmail.com
