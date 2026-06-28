from __future__ import annotations

import json
import urllib.request


def test_checkout_failure_scenario_resolves() -> None:
    request = urllib.request.Request("http://localhost:8080/scenario/checkout-deployment-failure", method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
    assert payload["incident"]["state"] == "resolved"
    assert payload["metrics"]["healthy"] is True
