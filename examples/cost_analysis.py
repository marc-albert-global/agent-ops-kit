"""Quantify the two token-efficiency levers the framework gives you.

1. On-demand routing. Instead of stuffing every skill and guide into the prompt
   on every call, the agent loads only the skills and guides relevant to the
   request. This is the main lever and it grows with workspace size: with 40
   skills, a request still loads only the two or three that apply.

2. Prompt caching. The stable prefix (framework instructions + loaded guides) is
   placed first and marked cache-eligible, so on repeated calls it is served at
   roughly one tenth of the input-token cost.

This script measures both across the example queries. Token counts use tiktoken
when available, otherwise a ~4-chars-per-token estimate (labeled either way).

Run from the repo root:  python examples/cost_analysis.py
"""

from agent_ops import Agent, EchoLLM


def _counter():
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return lambda s: len(enc.encode(s)), "tiktoken/cl100k_base"
    except Exception:
        return lambda s: max(1, len(s) // 4), "~4 chars/token estimate"


QUERIES = [
    "break down net new MRR, expansion vs new bookings this quarter",
    "how is gross vs net revenue retention trending year over year?",
    "where is the biggest drop-off in our signup-to-paid funnel?",
    "what changed in our activation funnel after Q1?",
]

# Anthropic Opus input pricing anchors (USD per 1M tokens). Cache reads ~0.1x.
PRICE_PER_M = 5.0
CACHE_READ_MULTIPLIER = 0.1


def main() -> None:
    count, method = _counter()
    agent = Agent.from_workspace("examples/saas_analyst", llm=EchoLLM())

    # "Load everything" cost: framework instructions + every skill + every guide.
    naive_tokens = count(agent.instructions)
    naive_tokens += sum(count(s.instructions) for s in agent.skills.skills)
    naive_tokens += sum(count(g.load()) for g in agent.guides.guides)

    routed_totals, stable, volatile = [], 0, 0
    for q in QUERIES:
        plan = agent.plan(q)
        routed_totals.append(sum(count(b.text) for b in plan.system))
        for block in plan.system:
            n = count(block.text)
            stable += n if block.stable else 0
            volatile += 0 if block.stable else n

    avg_routed = sum(routed_totals) / len(routed_totals)
    routing_reduction = (1 - avg_routed / naive_tokens) * 100 if naive_tokens else 0.0

    total = stable + volatile
    frac = stable / total if total else 0.0
    repeat_cost_ratio = frac * CACHE_READ_MULTIPLIER + (1 - frac)
    cache_reduction = (1 - repeat_cost_ratio) * 100

    print(f"Token-efficiency analysis over {len(QUERIES)} example queries")
    print(f"(token counts via {method}; workspace has "
          f"{len(agent.skills)} skills, {len(agent.guides)} guides)\n")

    print("1) On-demand routing (load-relevant vs load-everything)")
    print(f"   Load-everything prompt:  {naive_tokens:,} tokens")
    print(f"   Routed prompt (avg):     {avg_routed:,.0f} tokens")
    print(f"   => ~{routing_reduction:.0f}% fewer prompt tokens per call")
    print(f"   (this grows with workspace size: 40 skills still load only the few that match)\n")

    print("2) Prompt caching (stable prefix on warm-cache repeats)")
    print(f"   Cache-eligible share:    {frac*100:.0f}%")
    print(f"   => ~{cache_reduction:.0f}% input-cost reduction on repeated calls\n")

    print("Combined illustrative projection at 1,000 calls/day, Opus $5/1M input:")
    uncached_month = 1_000 * 30 * naive_tokens / 1_000_000 * PRICE_PER_M
    routed_month = 1_000 * 30 * avg_routed / 1_000_000 * PRICE_PER_M
    print(f"   load-everything ~${uncached_month:,.0f}/mo  ->  routed ~${routed_month:,.0f}/mo")
    print("   (Projection; caching saves further on repeat calls within the cache TTL.)")


if __name__ == "__main__":
    main()
