from agent_ops.guides import GuideLibrary


def test_loads_relevant_guide_only(workspace):
    lib = GuideLibrary.from_dir(workspace / "guides")
    relevant = lib.relevant("what is the exact formula for NRR and GRR?")
    names = [g.name for g in relevant]
    assert "metric-definitions" in names


def test_guide_body_loads(workspace):
    lib = GuideLibrary.from_dir(workspace / "guides")
    guide = next(g for g in lib.guides if g.name == "metric-definitions")
    assert "Net New MRR" in guide.load()


def test_irrelevant_query_loads_no_guide(workspace):
    lib = GuideLibrary.from_dir(workspace / "guides")
    assert lib.relevant("unrelated cooking recipe question") == []
