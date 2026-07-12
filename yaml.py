"""Tiny YAML compatibility shim for this scaffold's simple config file.

It implements only the small safe_load subset used by config/features.yaml so the
tracer bullet does not require a PyYAML installation. Replace with PyYAML when the
ML pipeline grows beyond scaffold validation.
"""

from __future__ import annotations

import json
from typing import Any, TextIO


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    try:
        return int(value)
    except ValueError:
        return value


def safe_load(stream: TextIO | str) -> dict[str, Any]:
    text = stream.read() if hasattr(stream, "read") else str(stream)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    last_key_at_indent: dict[int, tuple[Any, str]] = {}

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            item_text = line[2:].strip()
            if not isinstance(parent, list):
                container, key = last_key_at_indent[indent]
                new_list: list[Any] = []
                container[key] = new_list
                stack.append((indent, new_list))
                parent = new_list
            item_key, item_sep, item_value = item_text.partition(":")
            if item_sep:
                item: dict[str, Any] = {}
                parent.append(item)
                item_key = item_key.strip()
                if item_value.strip():
                    item[item_key] = _parse_scalar(item_value)
                else:
                    child = {}
                    item[item_key] = child
                stack.append((indent, item))
            else:
                parent.append(_parse_scalar(item_text))
            continue

        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"Unsupported YAML line: {raw_line}")
        key = key.strip()
        if value.strip():
            parent[key] = _parse_scalar(value)
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
            last_key_at_indent[indent + 2] = (parent, key)

    return root
