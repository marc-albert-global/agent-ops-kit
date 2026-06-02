from agent_ops.skills import SkillRegistry


def test_discovers_skills(workspace):
    reg = SkillRegistry.from_dir(workspace / "skills")
    names = {s.name for s in reg.skills}
    assert {"revenue-analysis", "churn-analysis", "funnel-conversion"} <= names


def test_routes_churn_query_to_churn_skill(workspace):
    reg = SkillRegistry.from_dir(workspace / "skills")
    matches = reg.route("how is our net revenue retention and churn trending?")
    assert matches, "expected at least one routed skill"
    assert matches[0].skill.name == "churn-analysis"


def test_routes_revenue_query_to_revenue_skill(workspace):
    reg = SkillRegistry.from_dir(workspace / "skills")
    matches = reg.route("break down net new MRR expansion vs new bookings")
    assert matches[0].skill.name == "revenue-analysis"


def test_irrelevant_query_routes_nothing(workspace):
    reg = SkillRegistry.from_dir(workspace / "skills")
    assert reg.route("what is the weather in Paris tomorrow") == []


def test_limit_caps_matches(workspace):
    reg = SkillRegistry.from_dir(workspace / "skills")
    matches = reg.route("revenue churn funnel conversion retention expansion", limit=2)
    assert len(matches) <= 2
