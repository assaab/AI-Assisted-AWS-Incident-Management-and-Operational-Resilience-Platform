from __future__ import annotations

import time
import urllib.request


def wait(url: str, timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status < 500:
                    return
        except Exception as exc:
            last_error = exc
        time.sleep(2)
    raise SystemExit(f"Timed out waiting for {url}: {last_error}")


if __name__ == "__main__":
    wait("http://localhost:8080/livez")
    wait("http://localhost:8080/readyz")
    wait("http://localhost:3000")
