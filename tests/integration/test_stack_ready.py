from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


def test_stack_readiness_endpoint() -> None:
    try:
        response = urllib.request.urlopen("http://localhost:8080/readyz", timeout=10)
    except urllib.error.URLError as exc:
        pytest.skip(f"unified API is not running on localhost:8080: {exc}")
    with response:
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
    assert payload["status"] in {"ready", "degraded"}
    assert "checks" in payload
