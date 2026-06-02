"""End-to-end demo of agent-ops-kit on the example SaaS-metrics workspace.

Run from the repo root:

    python examples/demo.py

Uses the offline echo backend unless ANTHROPIC_API_KEY is set, so it works
with no credentials.
"""

from agent_ops import Agent

QUERIES = [
    "break down net new MRR, expansion vs new bookings this quarter",
    "how is gross vs net revenue retention trending year over year?",
    "where is the biggest drop-off in our signup-to-paid funnel?",
]


def main() -> None:
    agent = Agent.from_workspace("examples/saas_analyst")
    print(f"Loaded '{agent.domain}' agent: "
          f"{len(agent.skills)} skills, {len(agent.guides)} guides, {len(agent.memory)} memories.\n")

    for q in QUERIES:
        print("=" * 72)
        print(agent.plan(q).summary())
        print()

    # Demonstrate the auto-learn loop.
    print("=" * 72)
    print("Teaching the agent a new fact...")
    mem = agent.learn(
        description="Annual plans now default to monthly billing",
        body="As of June 2026, annual contracts bill monthly by default unless prepaid.",
        type="project",
    )
    print(f"Stored memory: {mem.name} -> {mem.path}")
    recalled = agent.memory.recall("how are annual plans billed now?")
    print("Recall test:", [m.name for m in recalled])


if __name__ == "__main__":
    main()
