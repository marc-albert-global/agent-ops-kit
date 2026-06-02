from agent_ops import frontmatter


def test_parses_meta_and_body():
    doc = frontmatter.parse("---\nname: x\ntriggers: [a, b, c]\n---\n\nbody text here")
    assert doc.meta["name"] == "x"
    assert doc.meta["triggers"] == ["a", "b", "c"]
    assert doc.body == "body text here"


def test_no_frontmatter_returns_full_body():
    doc = frontmatter.parse("just a body, no fences")
    assert doc.meta == {}
    assert doc.body == "just a body, no fences"


def test_empty_list_value():
    doc = frontmatter.parse("---\ntriggers: []\n---\nbody")
    assert doc.meta["triggers"] == []
