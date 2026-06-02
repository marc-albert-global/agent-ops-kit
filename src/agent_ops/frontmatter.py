"""Minimal YAML frontmatter parser for markdown resource files.

Resources (skills, guides, memories) are plain markdown files with a small
YAML block between `---` fences at the top:

    ---
    name: revenue-analysis
    description: Analyze MRR, churn and expansion
    triggers: [mrr, churn, retention]
    ---
    <body instructions>

We keep the dependency surface small by parsing only the subset of YAML we
use (scalars and inline `[a, b]` lists). For anything richer, swap in PyYAML.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Document:
    meta: dict[str, object]
    body: str


def _coerce(value: str) -> object:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",")]
    return value.strip("\"'")


def parse(text: str) -> Document:
    """Split a markdown string into frontmatter metadata and body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return Document(meta={}, body=text.strip())

    meta: dict[str, object] = {}
    body_start = len(lines)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body_start = i + 1
            break
        line = lines[i]
        if not line.strip() or ":" not in line:
            continue
        key, _, raw = line.partition(":")
        meta[key.strip()] = _coerce(raw)

    body = "\n".join(lines[body_start:]).strip()
    return Document(meta=meta, body=body)
