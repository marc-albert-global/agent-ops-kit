"""The Agent orchestrator — ties the framework together.

A single `run(query)` does the work that makes this an *operations* agent
rather than a bare LLM call:

1. fire session-start hooks for orientation context (once),
2. route the request to the most relevant skills,
3. load only the reference guides the request actually needs,
4. recall relevant memories,
5. assemble an ordered system prompt (stable framework/domain/guide context
   first — cache-eligible — then volatile per-request context), and
6. complete via the configured LLM backend.

`plan(query)` runs steps 1–5 and returns the decisions without calling the
model, which is what `--dry-run` and the test-suite use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .guides import Guide, GuideLibrary
from .hooks import HookRegistry, default_orientation
from .llm import Completion, LLMClient, SystemBlock, default_llm
from .memory import Memory, MemoryStore
from .permissions import Permissions
from .skills import SkillMatch, SkillRegistry


@dataclass
class Plan:
    """The decisions the agent made for a request, before calling the model."""

    query: str
    orientation: list[str]
    skills: list[SkillMatch]
    guides: list[Guide]
    memories: list[Memory]
    system: list[SystemBlock]

    def summary(self) -> str:
        lines = [f"Query: {self.query}", ""]
        lines.append("Skills routed:")
        lines += [f"  • {m.skill.name} (score {m.score:.2f})" for m in self.skills] or ["  (none)"]
        lines.append("Guides loaded:")
        lines += [f"  • {g.name}" for g in self.guides] or ["  (none)"]
        lines.append("Memories recalled:")
        lines += [f"  • {m.name}" for m in self.memories] or ["  (none)"]
        stable = sum(1 for b in self.system if b.stable)
        lines.append("")
        lines.append(f"System prompt: {len(self.system)} blocks ({stable} cache-eligible).")
        return "\n".join(lines)


@dataclass
class Agent:
    domain: str
    instructions: str
    skills: SkillRegistry = field(default_factory=SkillRegistry)
    guides: GuideLibrary = field(default_factory=GuideLibrary)
    memory: MemoryStore | None = None
    permissions: Permissions = field(default_factory=Permissions)
    hooks: HookRegistry = field(default_factory=HookRegistry)
    llm: LLMClient = field(default_factory=default_llm)
    _oriented: bool = False
    _orientation: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Register the built-in orientation hook unless the caller already has hooks.
        if not self.hooks.session_start:
            self.hooks.on_session_start(default_orientation)

    # ---- construction -----------------------------------------------------

    @classmethod
    def from_workspace(cls, path: str | Path, *, llm: LLMClient | None = None) -> "Agent":
        """Load an agent from a workspace directory.

        Layout:
            agent.json            {"domain": ..., "instructions": ...}
            skills/*.md
            guides/*.md
            memory/*.md
            settings.json         durable permissions
            settings.local.json   local permission overrides (optional)
        """
        path = Path(path)
        config = json.loads((path / "agent.json").read_text(encoding="utf-8"))
        skills = SkillRegistry.from_dir(path / "skills") if (path / "skills").exists() else SkillRegistry()
        guides = GuideLibrary.from_dir(path / "guides") if (path / "guides").exists() else GuideLibrary()
        memory = MemoryStore.open(path / "memory")
        permissions = Permissions.load(path / "settings.json", path / "settings.local.json")
        return cls(
            domain=config.get("domain", "general"),
            instructions=config.get("instructions", ""),
            skills=skills,
            guides=guides,
            memory=memory,
            permissions=permissions,
            llm=llm or default_llm(),
        )

    # ---- orchestration ----------------------------------------------------

    def _orient(self) -> list[str]:
        if not self._oriented:
            self._orientation = self.hooks.run_session_start(self)
            self._oriented = True
        return self._orientation

    def plan(self, query: str) -> Plan:
        orientation = self._orient()
        matches = self.skills.route(query)
        loaded = self.guides.relevant(query)
        recalled = self.memory.recall(query) if self.memory else []

        system: list[SystemBlock] = []
        # --- stable prefix (cache-eligible): framework + domain + guides ---
        if self.instructions:
            system.append(SystemBlock(self.instructions, stable=True))
        if loaded:
            guide_text = "\n\n".join(f"## Guide: {g.name}\n{g.load()}" for g in loaded)
            system.append(SystemBlock("Reference guides:\n\n" + guide_text, stable=True))
        # --- volatile suffix: orientation, skills, memory, the request -----
        if orientation:
            system.append(SystemBlock("Orientation:\n" + "\n".join(orientation), stable=False))
        if matches:
            skill_text = "\n\n".join(
                f"## Skill: {m.skill.name}\n{m.skill.instructions}" for m in matches
            )
            system.append(SystemBlock("Applicable skills:\n\n" + skill_text, stable=False))
        if recalled:
            mem_text = "\n".join(f"- {m.description}: {m.body}" for m in recalled)
            system.append(SystemBlock("Relevant memory:\n" + mem_text, stable=False))

        return Plan(query, orientation, matches, loaded, recalled, system)

    def run(self, query: str) -> Completion:
        plan = self.plan(query)
        return self.llm.complete(plan.system, query)

    def learn(self, description: str, body: str, *, type: str = "note") -> Memory:
        if self.memory is None:
            raise RuntimeError("This agent has no memory store configured.")
        return self.memory.learn(description, body, type=type)
