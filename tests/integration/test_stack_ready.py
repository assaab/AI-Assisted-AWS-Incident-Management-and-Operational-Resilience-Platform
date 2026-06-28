from __future__ import annotations

import json
import urllib.request


def test_stack_readiness_endpoint() -> None:
    with urllib.request.urlopen("http://localhost:8080/readyz", timeout=10) as response:
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
    assert payload["status"] in {"ready", "degraded"}
    assert "checks" in payload
