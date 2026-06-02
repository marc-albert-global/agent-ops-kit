"""Session hooks.

Hooks let an integrator inject behavior at well-defined points in an agent's
lifecycle without modifying the core. The framework ships one lifecycle point —
`session_start` — which produces orientation context the agent prepends to its
system prompt (e.g. "you have N skills and M guides available").

Register a hook with the decorator; it receives the live `Agent` and returns a
string (added to context) or None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:  # avoid an import cycle; only needed for typing.
    from .agent import Agent

Hook = Callable[["Agent"], Optional[str]]


@dataclass
class HookRegistry:
    session_start: list[Hook] = field(default_factory=list)

    def on_session_start(self, fn: Hook) -> Hook:
        """Decorator: register a session-start hook."""
        self.session_start.append(fn)
        return fn

    def run_session_start(self, agent: "Agent") -> list[str]:
        out: list[str] = []
        for hook in self.session_start:
            result = hook(agent)
            if result:
                out.append(result)
        return out


def default_orientation(agent: "Agent") -> str:
    """Built-in session-start hook: summarize available capabilities."""
    return (
        f"You are operating in the '{agent.domain}' domain. "
        f"{len(agent.skills)} skills and {len(agent.guides)} reference guides are available, "
        f"loaded on demand. {len(agent.memory)} memories are on file."
    )
