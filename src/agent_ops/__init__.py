"""agent-ops-kit — a framework for domain-agnostic operations agents.

Build an LLM agent that routes requests to modular skills, loads reference
context on demand, learns to a persistent memory, and runs under a tiered
permission policy — on any domain, with the domain content kept entirely in a
workspace directory rather than in the framework.
"""

from .agent import Agent, Plan
from .guides import Guide, GuideLibrary
from .hooks import HookRegistry
from .llm import AnthropicLLM, Completion, EchoLLM, LLMClient, SystemBlock
from .memory import Memory, MemoryStore
from .permissions import Permissions
from .skills import Skill, SkillMatch, SkillRegistry

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Plan",
    "Skill",
    "SkillMatch",
    "SkillRegistry",
    "Guide",
    "GuideLibrary",
    "Memory",
    "MemoryStore",
    "Permissions",
    "HookRegistry",
    "LLMClient",
    "AnthropicLLM",
    "EchoLLM",
    "Completion",
    "SystemBlock",
]
