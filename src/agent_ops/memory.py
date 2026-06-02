"""File-based persistent memory with an auto-learn loop.

Each memory is one markdown file holding one durable fact, with frontmatter:

    ---
    name: q3-billing-cutover
    description: Billing system migrated to the new ledger in Q3
    type: project
    created: 2026-06-02
    ---
    <the fact>

The agent *recalls* memories relevant to a request (lexical scoring over the
description) and *learns* new memories from a run. Persistence is just the
filesystem — durable across process restarts, inspectable by a human, and
trivially version-controllable.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter
from ._match import relevance

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")[:60] or "memory"


@dataclass(frozen=True)
class Memory:
    name: str
    description: str
    body: str
    type: str = "note"
    created: str = ""
    path: Path | None = None

    @classmethod
    def from_file(cls, path: Path) -> "Memory":
        doc = frontmatter.parse(path.read_text(encoding="utf-8"))
        meta = doc.meta
        return cls(
            name=str(meta.get("name", path.stem)),
            description=str(meta.get("description", "")),
            body=doc.body,
            type=str(meta.get("type", "note")),
            created=str(meta.get("created", "")),
            path=path,
        )

    def to_markdown(self) -> str:
        return (
            "---\n"
            f"name: {self.name}\n"
            f"description: {self.description}\n"
            f"type: {self.type}\n"
            f"created: {self.created}\n"
            "---\n\n"
            f"{self.body}\n"
        )


@dataclass
class MemoryStore:
    directory: Path
    memories: list[Memory] = field(default_factory=list)

    @classmethod
    def open(cls, directory: str | Path) -> "MemoryStore":
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        memories = [
            Memory.from_file(p)
            for p in sorted(directory.glob("*.md"))
            if p.name.lower() != "readme.md"
        ]
        return cls(directory=directory, memories=memories)

    def recall(self, query: str, *, threshold: float = 0.3, limit: int = 3) -> list[Memory]:
        scored = [
            (m, relevance(query, text=f"{m.description} {m.body}"))
            for m in self.memories
        ]
        scored = [(m, s) for m, s in scored if s >= threshold]
        scored.sort(key=lambda ms: ms[1], reverse=True)
        return [m for m, _ in scored[:limit]]

    def learn(self, description: str, body: str, *, type: str = "note", name: str | None = None) -> Memory:
        """Persist a new fact and add it to the in-memory index."""
        name = name or slugify(description)
        memory = Memory(
            name=name,
            description=description,
            body=body,
            type=type,
            created=_dt.date.today().isoformat(),
            path=self.directory / f"{name}.md",
        )
        memory.path.write_text(memory.to_markdown(), encoding="utf-8")
        # Replace any existing memory with the same name.
        self.memories = [m for m in self.memories if m.name != name]
        self.memories.append(memory)
        return memory

    def __len__(self) -> int:
        return len(self.memories)
