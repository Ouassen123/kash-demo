"""Quick health check for the Habits test launch.

Checks:
- Frontend Next.js root page is reachable (default http://localhost:3000)
- FastAPI health endpoint is reachable (default http://localhost:8000/health)
- Frontend API base URL from frontend/.env.local points to the same backend and is reachable

Usage:
    python scripts/habits_health_check.py
    python scripts/habits_health_check.py --frontend http://localhost:3000 --api http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ENV = ROOT / "frontend" / ".env.local"


def load_api_base_url_from_env() -> str | None:
    if not FRONTEND_ENV.exists():
        return None

    for raw_line in FRONTEND_ENV.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "NEXT_PUBLIC_API_BASE_URL":
            return value.strip().rstrip("/")
    return None


def fetch_ok(url: str, timeout: int = 45) -> tuple[bool, str]:
    try:
        with urlopen(url, timeout=timeout) as response:
            body = response.read(256).decode("utf-8", errors="ignore")
            return True, f"HTTP {response.status} | {body[:120].replace(chr(10), ' ')}"
    except HTTPError as exc:
        return False, f"HTTP {exc.code} | {exc.reason}"
    except URLError as exc:
        return False, str(exc.reason)
    except Exception as exc:  # pragma: no cover - defensive CLI helper
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Habits launch health check")
    parser.add_argument("--frontend", default="http://localhost:3000", help="Frontend base URL")
    parser.add_argument("--api", default="http://localhost:8000", help="FastAPI base URL")
    args = parser.parse_args()

    frontend_root = args.frontend.rstrip("/")
    api_root = args.api.rstrip("/")
    api_health_url = f"{api_root}/health"
    frontend_api_base_url = load_api_base_url_from_env() or f"{api_root}/api/v1"
    configured_api_root = frontend_api_base_url[:-len("/api/v1")] if frontend_api_base_url.endswith("/api/v1") else frontend_api_base_url.rstrip("/")
    configured_api_health_url = f"{configured_api_root}/health"

    checks = [
        ("Frontend Next.js", frontend_root),
        ("FastAPI health", api_health_url),
        ("Frontend-configured API health", configured_api_health_url),
    ]

    print("Habits launch health check")
    print(f"- Frontend URL: {frontend_root}")
    print(f"- API URL: {api_root}")
    print(f"- Frontend NEXT_PUBLIC_API_BASE_URL: {frontend_api_base_url}")
    print()

    failures = 0
    for label, url in checks:
        ok, detail = fetch_ok(url)
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {label}: {url}")
        print(f"      {detail}")
        if not ok:
            failures += 1

    if frontend_api_base_url.endswith("/api/v1") and not frontend_api_base_url.startswith(api_root):
        failures += 1
        print("[FAIL] Frontend API base URL does not match the requested API root.")

    if failures:
        print(f"\nHealth check failed: {failures} issue(s) detected.")
        return 1

    print("\nHealth check passed: frontend and API are reachable and aligned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
