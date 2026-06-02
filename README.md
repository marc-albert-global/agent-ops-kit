# agent-ops-kit

A small, dependency-light framework for building **domain-agnostic LLM
operations agents** — the kind that sit next to a team, answer questions
against a body of domain knowledge, and get sharper with use.

It packages five patterns that turn a bare LLM call into an operations agent:

- **Skill routing** — modular units of domain instruction, auto-discovered and matched to each request, so only the relevant ones enter the prompt.
- **On-demand context loading** — long reference guides are indexed cheaply and loaded into context *only* when a request needs them.
- **Auto-learn memory** — a file-based memory the agent recalls from and writes back to, persistent across runs.
- **Tiered permissions** — a durable, shared policy layered with local, experimental overrides.
- **Session hooks** — lifecycle extension points (e.g. startup orientation).

The framework ships **zero** domain content. A domain lives entirely in a
*workspace directory* (skills, guides, memory, settings). The included example
is a neutral SaaS-metrics analyst; point it at a different workspace and it's a
different agent.

> Built as a clean-room generalization of a production internal operations
> agent. No proprietary data — the patterns are the point.

---

## Why it exists

A single `messages.create()` call is stateless and context-blind: it can't
decide *which* of your 40 playbooks applies, it has no memory of last week, and
naïvely stuffing every guide into the system prompt is slow and expensive. This
framework adds the routing/loading/memory layer around the call — and keeps the
expensive, stable context cache-friendly so repeated requests are cheap.

```
                         ┌──────────────────────────────────────────┐
   request ─────────────▶│                  Agent                    │
                         │                                            │
                         │  hooks ──▶ orientation                     │
                         │  skills ─▶ route to relevant skills        │
                         │  guides ─▶ load only what's needed         │
                         │  memory ─▶ recall relevant facts           │
                         │                                            │
                         │  assemble system prompt:                   │
                         │    [ framework + domain + guides ]  ◀─ cache-eligible (stable)
                         │    [ orientation + skills + memory ] ◀─ volatile (per-request)
                         └───────────────────┬────────────────────────┘
                                             ▼
                                    LLM backend (Anthropic / Echo)
                                             │
                          completion ◀───────┘   (optionally: learn() a new memory)
```

The stable blocks are placed first and carry the prompt-cache breakpoint, so
the framework instructions, domain config, and loaded guides are served from
cache on repeated requests while the per-request context stays uncached.

---

## Install

```bash
git clone https://github.com/MarcAlbert06800/agent-ops-kit.git
cd agent-ops-kit
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # core + test deps; no API key needed
# For real model completions:
pip install -e ".[anthropic]" && export ANTHROPIC_API_KEY=sk-ant-...
```

Python 3.9+. The core has **no runtime dependencies** — the Anthropic SDK is an
optional extra. With no key, the agent uses a deterministic offline backend so
everything is runnable and testable out of the box.

## Quickstart (CLI)

```bash
# List the skills discovered in the example workspace
agent-ops skills

# Show the routing decisions for a request — which skills, guides, memories
agent-ops plan "break down net new MRR — expansion vs new bookings this quarter"

# Run the full pipeline (offline echo backend)
agent-ops run --dry-run "how is gross vs net revenue retention trending?"

# Run against the real model (requires ANTHROPIC_API_KEY)
agent-ops run "how is gross vs net revenue retention trending?"
```

`plan` output for the first request:

```
Skills routed:
  • revenue-analysis (score 1.30)
  • churn-analysis (score 0.30)
Memories recalled:
  • expansion-revenue-priority
System prompt: 4 blocks (1 cache-eligible).
```

## Quickstart (library)

```python
from agent_ops import Agent

agent = Agent.from_workspace("examples/saas_analyst")

# See what the agent would do (no model call)
print(agent.plan("how is churn trending?").summary())

# Run it (uses the real model if ANTHROPIC_API_KEY is set, else the echo backend)
completion = agent.run("how is churn trending?")
print(completion.text)

# Teach it something durable — recalled on future relevant requests
agent.learn(
    description="Pricing rose 10% on the Pro tier in June",
    body="List price on the Pro tier increased from $40 to $44/seat in June 2026.",
    type="project",
)
```

## Build your own agent

Create a workspace directory:

```
my_agent/
├── agent.json            # { "domain": "...", "instructions": "..." }
├── skills/               # one markdown file per skill (frontmatter + body)
├── guides/               # long-form reference material, loaded on demand
├── memory/               # persistent facts (the agent also writes here)
├── settings.json         # durable permissions
└── settings.local.json   # local overrides (gitignore this)
```

A skill is just markdown with frontmatter:

```markdown
---
name: incident-triage
description: Triage and prioritize production incidents by severity
triggers: [incident, outage, sev1, pager, downtime]
---
When triaging an incident: classify severity first (Sev1–Sev3), ...
```

Then: `Agent.from_workspace("my_agent")`. No framework code changes.

## Design

See [ARCHITECTURE.md](ARCHITECTURE.md) for the module breakdown, the routing
algorithm, and the prompt-cache strategy.

## Tests

```bash
pytest          # 26 tests, runs fully offline
```

## License

MIT © 2026 Marc Albert
