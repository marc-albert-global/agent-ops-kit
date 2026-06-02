from agent_ops.permissions import Permissions


def test_merge_and_wildcard(workspace):
    perms = Permissions.load(workspace / "settings.json", workspace / "settings.local.json")
    assert perms.is_allowed("metrics:read:mrr")        # wildcard allow
    assert perms.is_allowed("memory:write:note")        # granted by local layer
    assert not perms.is_allowed("metrics:write:mrr")    # explicit deny
    assert not perms.is_allowed("data:export:raw")      # explicit deny


def test_default_deny():
    perms = Permissions(allow=["a:*"], deny=[])
    assert perms.is_allowed("a:x")
    assert not perms.is_allowed("b:x")


def test_deny_beats_allow():
    perms = Permissions(allow=["x:*"], deny=["x:secret"])
    assert perms.is_allowed("x:public")
    assert not perms.is_allowed("x:secret")
