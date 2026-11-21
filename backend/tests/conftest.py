import os
import sys
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="shifttrace-test-"))
os.environ["SHIFTTRACE_DB"] = str(_tmp / "test.db")
os.environ["APPROVAL_WAIT_S"] = "0.6"
os.environ["MCP_TOKEN"] = "test-token"
os.environ["CAPTURE_DELAY_S"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from app.seed import reset_database  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    reset_database()
    yield
