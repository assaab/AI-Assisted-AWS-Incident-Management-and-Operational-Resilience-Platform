from __future__ import annotations

import json
import os
import urllib.request


def main() -> None:
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8080").rstrip("/")
    request = urllib.request.Request(f"{api_base_url}/scenario/checkout-deployment-failure", method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    incident = payload["incident"]
    if incident["state"] != "resolved":
        raise SystemExit(f"Scenario did not resolve: {incident['state']}")
    print(json.dumps({"incident_id": incident["incident_id"], "state": incident["state"]}, indent=2))


if __name__ == "__main__":
    main()
