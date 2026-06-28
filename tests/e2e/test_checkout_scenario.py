from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


def test_checkout_failure_scenario_resolves() -> None:
    request = urllib.request.Request("http://localhost:8080/scenario/checkout-deployment-failure", method="POST")
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.URLError as exc:
        pytest.skip(f"unified API is not running on localhost:8080: {exc}")
    with response:
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
    assert payload["incident"]["state"] == "resolved"
    assert payload["metrics"]["healthy"] is True
