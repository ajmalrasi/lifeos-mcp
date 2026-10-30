"""Audit the complete application GET catalog, including the one stateful exception."""

import json
from pathlib import Path

from lifeos_mcp.client import DYNAMIC_ROUTES, READ_ROUTES


def test_all_audited_gets_are_covered_or_explicitly_excluded():
    audited = set(
        json.loads((Path(__file__).parent / "fixtures/backend-get-paths.json").read_text())
    )
    exposed = set(READ_ROUTES.values()) | set(DYNAMIC_ROUTES.values())
    assert len(exposed) == 38
    assert audited - exposed == {"/mail/accounts"}
    assert exposed <= audited
