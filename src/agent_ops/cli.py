"""Command-line interface for agent-ops-kit.

    agent-ops run "<query>" [--workspace DIR] [--dry-run]
    agent-ops skills [--workspace DIR]
    agent-ops memory [--workspace DIR]
    agent-ops plan "<query>" [--workspace DIR]

`run` without an ANTHROPIC_API_KEY (or with --dry-run) uses the offline echo
backend, so the tool is fully demonstrable with no credentials.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import Agent
from .llm import EchoLLM

DEFAULT_WORKSPACE = Path("examples/saas_analyst")


def _load(workspace: str, *, dry_run: bool = False) -> Agent:
    llm = EchoLLM() if dry_run else None
    return Agent.from_workspace(workspace, llm=llm)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-ops", description="Operations-agent framework.")
    parser.add_argument("--workspace", "-w", default=str(DEFAULT_WORKSPACE), help="Workspace directory.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Answer a request through the full pipeline.")
    p_run.add_argument("query")
    p_run.add_argument("--dry-run", action="store_true", help="Use the offline echo backend.")

    p_plan = sub.add_parser("plan", help="Show routing decisions without calling the model.")
    p_plan.add_argument("query")

    sub.add_parser("skills", help="List discovered skills.")
    sub.add_parser("memory", help="List stored memories.")

    args = parser.parse_args(argv)

    if args.command == "skills":
        agent = _load(args.workspace, dry_run=True)
        print(f"{len(agent.skills)} skills in {args.workspace}:")
        for s in agent.skills.skills:
            print(f"  • {s.name}, {s.description}")
        return 0

    if args.command == "memory":
        agent = _load(args.workspace, dry_run=True)
        print(f"{len(agent.memory)} memories in {args.workspace}:")
        for m in agent.memory.memories:
            print(f"  • [{m.type}] {m.name}, {m.description}")
        return 0

    if args.command == "plan":
        agent = _load(args.workspace, dry_run=True)
        print(agent.plan(args.query).summary())
        return 0

    if args.command == "run":
        agent = _load(args.workspace, dry_run=args.dry_run)
        print(agent.plan(args.query).summary())
        print("\n===== completion =====\n")
        completion = agent.run(args.query)
        print(completion.text)
        if completion.usage:
            print(f"\n[usage: {completion.usage}]")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
