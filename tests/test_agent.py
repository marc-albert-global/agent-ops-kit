from agent_ops import Agent, EchoLLM
from agent_ops.llm import SystemBlock


def test_on_demand_routing_is_smaller_than_loading_everything(workspace):
    """The core efficiency lever: a routed prompt is materially smaller than
    loading every skill and guide on every call (measured in characters to stay
    dependency-free; cost_analysis.py reports the token-level figure)."""
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    load_everything = (
        len(agent.instructions)
        + sum(len(s.instructions) for s in agent.skills.skills)
        + sum(len(g.load()) for g in agent.guides.guides)
    )
    routed = sum(len(b.text) for b in agent.plan("how is churn and net revenue retention trending?").system)
    assert routed < load_everything


def test_plan_assembles_stable_prefix_then_volatile(workspace):
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    plan = agent.plan("break down net new MRR: expansion vs new")

    # Stable blocks (framework instructions, guides) must precede volatile ones.
    stable_idx = [i for i, b in enumerate(plan.system) if b.stable]
    volatile_idx = [i for i, b in enumerate(plan.system) if not b.stable]
    assert stable_idx, "expected a stable prefix"
    assert max(stable_idx) < min(volatile_idx), "stable blocks must come first"

    # Revenue query routes the revenue skill and recalls the expansion memory.
    assert any(m.skill.name == "revenue-analysis" for m in plan.skills)
    assert any(m.name == "expansion-revenue-priority" for m in plan.memories)


def test_run_uses_echo_backend_offline(workspace):
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    completion = agent.run("how is churn trending this quarter?")
    assert completion.model == "echo"
    assert "churn" in completion.text.lower()


def test_orientation_hook_fires_once(workspace):
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    agent.plan("q1")
    first = agent._orientation
    agent.plan("q2")
    assert agent._orientation is first  # cached, not recomputed


def test_anthropic_block_builder_marks_last_stable_block():
    # Verify the cache breakpoint lands on the last stable block without a key.
    from agent_ops.llm import AnthropicLLM

    blocks = [SystemBlock("framework", stable=True), SystemBlock("guides", stable=True), SystemBlock("request ctx", stable=False)]
    built = AnthropicLLM.__dict__["_build_system"](object.__new__(AnthropicLLM), blocks)
    assert "cache_control" not in built[0]
    assert built[1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in built[2]
