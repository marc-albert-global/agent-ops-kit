# agent-ops-kit

[![CI](https://github.com/marc-albert-global/agent-ops-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/marc-albert-global/agent-ops-kit/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![lint: ruff](https://img.shields.io/badge/lint-ruff-261230)
![types: mypy](https://img.shields.io/badge/types-mypy-2a6db2)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Stand up a domain expert AI agent for a team without rebuilding the plumbing,
and keep its token bill flat as it grows.** A framework for "operations analyst"
agents that route each request to the right playbook, load only the reference
material that request needs, learn across sessions, and run under a permission
policy you can actually ship.

It exists because the hard part of deploying an LLM agent into a real
organization is not the model call. It is keeping a large, evolving body of
domain knowledge usable and affordable: loading the right slice per request,
not paying for all of it every time, and giving operators control over what the
agent may do.

> Scope: a working framework with a neutral example workspace (SaaS-metrics
> analyst). The patterns, not a specific domain agent, are the deliverable.

---

## Impact at a glance

| | |
|---|---|
| Prompt size per call | **~49% fewer tokens** vs. loading every skill and guide (on-demand routing) |
| Scaling property | the saving grows with the workspace: 40 skills still load only the few that match |
| Repeat-call cost | stable prefix is cache-eligible, **~18% further input-cost cut** on warm-cache repeats |
| Dependencies | **zero** runtime deps in the core; fully runnable and testable offline |
| Extensibility | a new domain is a folder of files, not a code change |

Numbers from `python examples/cost_analysis.py` on the example workspace; the
routing saving rises sharply with more skills/guides.

---

## Problem and context

Drop an LLM agent into a company and you hit three walls fast. (1) The domain
knowledge is large and grows, so stuffing every playbook into every prompt is
slow and expensive. (2) The agent has no memory of last week. (3) Letting it do
anything is a non-starter for a cautious buyer. Teams end up rebuilding the same
routing/loading/memory/permission scaffolding for each new agent. This framework
is that scaffolding, done once, with the domain content kept entirely outside
the code.

## Approach

Five patterns turn a bare `messages.create()` into a deployable operations agent:

- **Skill routing**: modular units of domain instruction, auto-discovered and matched to each request, so only the relevant ones enter the prompt.
- **On-demand context loading**: long reference guides are indexed cheaply and read into context only when a request needs them.
- **Auto-learn memory**: a file-based memory the agent recalls from and writes back to, persistent across runs.
- **Tiered permissions**: a durable shared policy layered with local experimental overrides, so rollout is governed.
- **Session hooks**: lifecycle extension points (e.g. startup orientation).

A domain lives entirely in a *workspace directory* (skills, guides, memory,
settings). Point the agent at a different workspace and it is a different agent.

```
request -> hooks (orientation) -> route to relevant skills -> load only needed guides
        -> recall relevant memory -> assemble [stable prefix | volatile tail] -> LLM
```

The stable prefix (framework instructions + loaded guides) is placed first and
marked cache-eligible; the volatile tail (orientation, routed skills, memory)
follows. That layout is what makes repeat calls cheap.

## From demo to deployment

How this maps to a real agent engagement:

- **Onboard a client domain as a workspace**, not a fork. Their analysts' playbooks become skills; their reference docs become guides; nothing in the framework changes.
- **Cost stays bounded as scope grows.** Routing means adding the 41st skill does not inflate every prompt; only matched skills load. This is the property that keeps a growing agent affordable.
- **Permission tiers gate rollout.** Start read-only (`deny` writes), widen per capability as trust builds, with a durable shared policy plus local overrides.
- **Memory makes it improve in place.** Confirmed answers and corrections persist and are recalled, so the agent gets sharper without redeployment.
- **Decision rule for backends.** The `LLMClient` protocol lets you run the real model in production and a deterministic offline backend in CI and demos, with no API key.

## Quickstart

```bash
git clone https://github.com/marc-albert-global/agent-ops-kit.git
cd agent-ops-kit
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"            # core + tests, no API key needed

agent-ops skills                                   # list discovered skills
agent-ops plan "how is net revenue retention trending?"   # show routing decisions
agent-ops run --dry-run "how is churn trending?"   # full pipeline, offline backend
python examples/cost_analysis.py                   # token-efficiency numbers
ruff check src tests && mypy && pytest -q          # lint + type-check + 35 tests, offline
```

For real completions: `pip install -e ".[anthropic]" && export ANTHROPIC_API_KEY=sk-ant-...`

## Add a domain (no code change)

```
my_agent/
├── agent.json            # { "domain": "...", "instructions": "..." }
├── skills/               # one markdown file per skill (frontmatter + body)
├── guides/               # long-form reference, loaded on demand
├── memory/               # persistent facts (the agent writes here too)
├── settings.json         # durable permissions
└── settings.local.json   # local overrides (gitignored)
```

Then `Agent.from_workspace("my_agent")`. See [ARCHITECTURE.md](ARCHITECTURE.md)
for the routing algorithm and prompt-cache strategy.

## Methodology

- Routing/recall use an explainable lexical relevance score (no opaque embedding step), so a routing decision can be read and understood; swapping in embeddings means replacing one function.
- The token-efficiency figures come from `examples/cost_analysis.py`, and the routing-is-smaller property is enforced by a test.
- Prompt caching follows the prefix-match rule: stable content first, single breakpoint on the last stable block.

## Limitations

- Lexical routing can miss paraphrases an embedding model would catch; it is a deliberate simplicity/explainability trade.
- No multi-step tool-use loop yet; this is the context-and-routing layer, not a full agent runtime.
- The example workspace is intentionally small, so its absolute token numbers are modest; the routing saving is what scales.

## Roadmap

- Optional embedding-based routing behind the same interface.
- A routing-precision eval harness (did the right skill fire?).
- A multi-step tool-use loop on top of the context layer.
- More backends behind the `LLMClient` protocol.

## License

MIT © 2026 Marc Albert
