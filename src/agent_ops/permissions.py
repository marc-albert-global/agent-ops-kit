"""Tiered permission configuration.

Two layers are merged at load time, mirroring the durable-vs-experimental
split that keeps a shared, reviewed policy separate from local one-off grants:

- `settings.json`        — durable, shared, checked into version control.
- `settings.local.json`  — personal/experimental, gitignored, overrides durable.

A permission entry is a string pattern. `allow` grants, `deny` always wins.
Patterns support a trailing `*` wildcard (e.g. ``"web:read:*"``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def _matches(pattern: str, action: str) -> bool:
    if pattern == action:
        return True
    if pattern.endswith("*"):
        return action.startswith(pattern[:-1])
    return False


@dataclass
class Permissions:
    allow: list[str] = field(default_factory=list)
    deny: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, durable: str | Path, local: str | Path | None = None) -> "Permissions":
        allow: list[str] = []
        deny: list[str] = []
        for path in (durable, local):
            if path is None:
                continue
            path = Path(path)
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            perms = data.get("permissions", data)
            allow.extend(perms.get("allow", []))
            deny.extend(perms.get("deny", []))
        # De-dup, preserve order.
        return cls(allow=list(dict.fromkeys(allow)), deny=list(dict.fromkeys(deny)))

    def is_allowed(self, action: str) -> bool:
        """Deny wins over allow; default-deny if no allow rule matches."""
        if any(_matches(p, action) for p in self.deny):
            return False
        return any(_matches(p, action) for p in self.allow)
