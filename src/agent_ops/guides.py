"""On-demand reference-guide loading.

Guides are long-form reference material (methodology, domain facts, formats)
that would blow the context budget if loaded wholesale on every request. The
GuideLibrary indexes each guide by lightweight keywords and only reads a
guide's full text into context when the request is relevant to it.

This separates *routing* (always cheap — descriptions and keywords) from
*loading* (pay the tokens only when needed), which is what keeps a
many-domain agent affordable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter
from ._match import relevance


@dataclass(frozen=True)
class Guide:
    name: str
    description: str
    keywords: tuple[str, ...]
    path: Path
    _body: str = ""

    @classmethod
    def from_file(cls, path: Path) -> "Guide":
        doc = frontmatter.parse(path.read_text(encoding="utf-8"))
        meta = doc.meta
        keywords = meta.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        return cls(
            name=str(meta.get("name", path.stem)),
            description=str(meta.get("description", "")),
            keywords=tuple(str(k) for k in keywords),
            path=path,
            _body=doc.body,
        )

    def load(self) -> str:
        """Return the full guide text. Re-read from disk if not cached."""
        if self._body:
            return self._body
        return frontmatter.parse(self.path.read_text(encoding="utf-8")).body


@dataclass
class GuideLibrary:
    guides: list[Guide] = field(default_factory=list)

    @classmethod
    def from_dir(cls, directory: str | Path) -> "GuideLibrary":
        directory = Path(directory)
        guides = [
            Guide.from_file(p)
            for p in sorted(directory.glob("*.md"))
            if p.name.lower() not in {"readme.md", "index.md"}
        ]
        return cls(guides=guides)

    def relevant(self, query: str, *, threshold: float = 0.3, limit: int = 2) -> list[Guide]:
        scored = [
            (g, relevance(query, text=f"{g.name} {g.description}", keywords=g.keywords))
            for g in self.guides
        ]
        scored = [(g, s) for g, s in scored if s >= threshold]
        scored.sort(key=lambda gs: gs[1], reverse=True)
        return [g for g, _ in scored[:limit]]

    def __len__(self) -> int:
        return len(self.guides)
