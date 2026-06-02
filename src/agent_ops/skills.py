"""Skill discovery and routing.

A *skill* is a self-contained unit of domain instruction stored as a markdown
file. Skills are auto-discovered from a directory and matched to an incoming
request by lexical relevance, so only the handful of skills that actually
apply to a request are loaded into the model's context.

This is the on-demand-loading pattern: the registry knows about every skill's
*description* cheaply, but a skill's full *instructions* only enter the prompt
when the router selects it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter
from ._match import relevance


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    triggers: tuple[str, ...]
    instructions: str
    path: Path | None = None

    @classmethod
    def from_file(cls, path: Path) -> Skill:
        doc = frontmatter.parse(path.read_text(encoding="utf-8"))
        meta = doc.meta
        raw = meta.get("triggers", [])
        items: list = [raw] if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
        return cls(
            name=str(meta.get("name", path.stem)),
            description=str(meta.get("description", "")),
            triggers=tuple(str(t) for t in items),
            instructions=doc.body,
            path=path,
        )


@dataclass
class SkillMatch:
    skill: Skill
    score: float


@dataclass
class SkillRegistry:
    skills: list[Skill] = field(default_factory=list)

    @classmethod
    def from_dir(cls, directory: str | Path) -> SkillRegistry:
        directory = Path(directory)
        skills = [
            Skill.from_file(p)
            for p in sorted(directory.glob("*.md"))
            if p.name.lower() != "readme.md"
        ]
        return cls(skills=skills)

    def route(self, query: str, *, threshold: float = 0.3, limit: int = 3) -> list[SkillMatch]:
        """Return the most relevant skills for a request, best first.

        `threshold` filters out incidental matches; `limit` caps how many
        skills' instructions get loaded so the prompt stays focused.
        """
        scored = [
            SkillMatch(
                skill=s,
                score=relevance(query, text=f"{s.name} {s.description}", keywords=s.triggers),
            )
            for s in self.skills
        ]
        scored = [m for m in scored if m.score >= threshold]
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:limit]

    def __len__(self) -> int:
        return len(self.skills)
