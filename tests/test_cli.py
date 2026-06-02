"""CLI smoke tests, run against the example workspace (offline echo backend)."""

from agent_ops.cli import main


def test_cli_skills_lists_skills(capsys):
    assert main(["skills"]) == 0
    assert "revenue-analysis" in capsys.readouterr().out


def test_cli_plan_shows_routing(capsys):
    assert main(["plan", "how is churn and net revenue retention trending?"]) == 0
    out = capsys.readouterr().out
    assert "churn-analysis" in out


def test_cli_run_dry_uses_echo_backend(capsys):
    assert main(["run", "--dry-run", "break down net new MRR"]) == 0
    assert "EchoLLM" in capsys.readouterr().out


def test_cli_memory_lists_memories(capsys):
    assert main(["memory"]) == 0
    assert "memories in" in capsys.readouterr().out
