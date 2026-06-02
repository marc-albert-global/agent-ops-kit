from agent_ops.memory import MemoryStore, slugify


def test_slugify():
    assert slugify("Q3 Billing Cutover!") == "q3-billing-cutover"


def test_recall_relevant_memory(workspace):
    store = MemoryStore.open(workspace / "memory")
    recalled = store.recall("how should I treat expansion revenue this year?")
    assert any(m.name == "expansion-revenue-priority" for m in recalled)


def test_learn_and_recall_roundtrip(tmp_path):
    store = MemoryStore.open(tmp_path)
    assert len(store) == 0
    store.learn("Pricing changed in June", "List price rose 10% on the Pro tier.", type="project")
    recalled = store.recall("did the pricing change recently?")
    assert recalled and "Pro tier" in recalled[0].body
    # Persisted to disk.
    assert (tmp_path / "pricing-changed-in-june.md").exists()


def test_learn_replaces_same_name(tmp_path):
    store = MemoryStore.open(tmp_path)
    store.learn("a fact", "old body", name="fixed")
    store.learn("a fact", "new body", name="fixed")
    assert len(store) == 1
    assert store.memories[0].body == "new body"
