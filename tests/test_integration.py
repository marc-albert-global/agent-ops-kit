"""Integration paths not covered by the per-module tests."""

from agent_ops import Agent, EchoLLM
from agent_ops.hooks import default_orientation
from agent_ops.llm import SystemBlock


def test_echo_llm_surfaces_assembled_context():
    llm = EchoLLM()
    completion = llm.complete([SystemBlock("a stable instruction", stable=True)], "a question")
    assert completion.model == "echo"
    assert "a stable instruction" in completion.text
    assert "a question" in completion.text


def test_default_orientation_mentions_domain_and_capabilities(workspace):
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    text = default_orientation(agent)
    assert agent.domain in text
    assert "skills" in text and "memories" in text


def test_permissions_are_wired_from_workspace(workspace):
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    assert agent.permissions.is_allowed("metrics:read:mrr")     # durable allow
    assert agent.permissions.is_allowed("memory:write:note")    # local-layer allow
    assert not agent.permissions.is_allowed("metrics:write:mrr")  # explicit deny


def test_memory_recall_is_empty_for_irrelevant_query(workspace):
    agent = Agent.from_workspace(workspace, llm=EchoLLM())
    assert agent.memory is not None
    assert agent.memory.recall("unrelated astrophysics neutron star question") == []
