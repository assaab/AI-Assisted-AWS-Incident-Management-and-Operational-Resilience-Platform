from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any


def _request_json(url: str, method: str = "GET") -> dict[str, Any] | list[dict[str, Any]]:
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    api_url = os.getenv("API_URL", "http://localhost:8080").rstrip("/")
    incidents = _request_json(f"{api_url}/incidents")
    if not isinstance(incidents, list):
        raise SystemExit("Incident API returned an unexpected payload")
    candidates = [
        item
        for item in incidents
        if item.get("state") == "resolved" and item.get("metadata", {}).get("service") == "checkout-service"
    ]
    if not candidates:
        raise SystemExit("No resolved checkout-service incident found. Run make scenario-checkout-failure first.")
    incident_id = str(candidates[0]["incident_id"])
    report = _request_json(f"{api_url}/incidents/{incident_id}/report", method="POST")
    if not isinstance(report, dict):
        raise SystemExit("Report API returned an unexpected payload")
    artifact_dir = Path("artifacts/latest")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "executive-summary.md").write_text(str(report["executive_summary"]), encoding="utf-8")
    (artifact_dir / "post-incident-review.md").write_text(str(report["post_incident_review"]), encoding="utf-8")
    (artifact_dir / "incident-timeline.json").write_text(
        json.dumps(report["incident_timeline"], indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"incident_id": incident_id, "artifact_dir": str(artifact_dir)}, indent=2))


if __name__ == "__main__":
    main()
