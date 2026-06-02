from pathlib import Path

import pytest

WORKSPACE = Path(__file__).resolve().parents[1] / "examples" / "saas_analyst"


@pytest.fixture
def workspace() -> Path:
    return WORKSPACE
