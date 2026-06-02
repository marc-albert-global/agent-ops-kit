"""LLM client abstraction.

The agent talks to an LLM through a tiny protocol so the orchestration logic
(routing, guide loading, memory, prompt assembly) is testable offline and the
model backend is swappable.

- `AnthropicLLM` calls the real Anthropic Messages API. It builds the system
  prompt as an ordered list of blocks and places a `cache_control` breakpoint
  on the last *stable* block, so the framework instructions + domain config +
  loaded guides are served from cache on repeated requests while the volatile
  per-request context stays after the breakpoint.
- `EchoLLM` is a deterministic offline backend used for tests and for
  `--dry-run`, so the framework is fully exercisable with no API key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# Current most capable model. Adaptive thinking + effort per the Anthropic SDK.
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass
class SystemBlock:
    """One block of the system prompt. `stable` blocks are cache-eligible."""

    text: str
    stable: bool = True


@dataclass
class Completion:
    text: str
    model: str = ""
    usage: dict = field(default_factory=dict)


class LLMClient(Protocol):
    def complete(self, system: list[SystemBlock], user: str) -> Completion: ...


class EchoLLM:
    """Offline backend. Returns a structured echo of what it was asked.

    Deterministic, no network, no key, lets the whole pipeline run in tests
    and dry-runs. It surfaces the assembled context so you can *see* the
    routing decisions the framework made.
    """

    model = "echo"

    def complete(self, system: list[SystemBlock], user: str) -> Completion:
        stable = sum(1 for b in system if b.stable)
        preview = "\n\n".join(b.text for b in system)
        text = (
            "[EchoLLM, offline backend; set ANTHROPIC_API_KEY for real completions]\n\n"
            f"Request: {user}\n\n"
            f"Assembled system prompt: {len(system)} blocks ({stable} cache-eligible).\n"
            "----- begin system context -----\n"
            f"{preview}\n"
            "----- end system context -----"
        )
        return Completion(text=text, model=self.model, usage={"backend": "echo"})


class AnthropicLLM:
    """Real backend using the Anthropic Messages API with prompt caching."""

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "high", api_key: str | None = None):
        import anthropic  # imported lazily so the package works without it installed

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def _build_system(self, system: list[SystemBlock]) -> list[dict]:
        """Order stable blocks first and cache-mark the last stable one.

        Caching is a prefix match, so all stable content must physically
        precede the volatile content, and the single breakpoint goes on the
        last stable block (caching everything up to and including it).
        """
        stable = [b for b in system if b.stable]
        volatile = [b for b in system if not b.stable]
        blocks: list[dict] = []
        for i, b in enumerate(stable):
            block = {"type": "text", "text": b.text}
            if i == len(stable) - 1:  # last stable block carries the breakpoint
                block["cache_control"] = {"type": "ephemeral"}
            blocks.append(block)
        for b in volatile:
            blocks.append({"type": "text", "text": b.text})
        return blocks

    def complete(self, system: list[SystemBlock], user: str) -> Completion:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            system=self._build_system(system),
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0),
            "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0),
        }
        return Completion(text=text, model=resp.model, usage=usage)


def default_llm() -> LLMClient:
    """Pick a real backend if `anthropic` + a key are present, else EchoLLM."""
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return EchoLLM()
    try:
        return AnthropicLLM()
    except Exception:
        return EchoLLM()
