"""One-shot final verification runner for Epic 5 deliverables.

Usage:
    python scripts/run_epic5_final_checks.py
    python scripts/run_epic5_final_checks.py --skip-docker
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckCommand:
    name: str
    command: List[str]
    cwd: Path
    optional: bool = False


@dataclass
class CheckResult:
    name: str
    status: str  # pass / fail / skipped
    return_code: Optional[int] = None


def run_check(item: CheckCommand) -> CheckResult:
    print(f"\n=== {item.name} ===")
    print(f"$ {' '.join(item.command)}")
    try:
        completed = subprocess.run(
            item.command,
            cwd=str(item.cwd),
            check=False,
            text=True,
        )
    except FileNotFoundError:
        status = "skipped" if item.optional else "fail"
        print(f"Command not found: {item.command[0]}")
        return CheckResult(name=item.name, status=status, return_code=None)

    if completed.returncode == 0:
        return CheckResult(name=item.name, status="pass", return_code=0)

    status = "skipped" if item.optional else "fail"
    return CheckResult(name=item.name, status=status, return_code=completed.returncode)


def build_checks(skip_docker: bool) -> List[CheckCommand]:
    checks = [
        CheckCommand(
            name="Backend performance optimization suite",
            command=["python", "test_performance_optimization.py"],
            cwd=PROJECT_ROOT,
        ),
        CheckCommand(
            name="Final validation automation",
            command=["python", "scripts/run_final_validation.py"],
            cwd=PROJECT_ROOT,
        ),
        CheckCommand(
            name="QA smoke tests",
            command=["python", "-m", "pytest", "test_final_validation_qa.py", "test_admin_reporting.py"],
            cwd=PROJECT_ROOT,
        ),
        CheckCommand(
            name="Frontend lint",
            command=["npm", "run", "lint"],
            cwd=PROJECT_ROOT / "frontend",
        ),
    ]

    docker_optional = skip_docker or shutil.which("docker") is None
    checks.append(
        CheckCommand(
            name="Pilot docker compose config",
            command=["docker", "compose", "-f", "infrastructure/pilot/docker-compose.pilot.yml", "config"],
            cwd=PROJECT_ROOT,
            optional=docker_optional,
        )
    )
    return checks


def print_summary(results: List[CheckResult]) -> int:
    print("\n\n========== EPIC 5 FINAL CHECK SUMMARY ==========")
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skipped")

    for result in results:
        marker = "✅" if result.status == "pass" else ("⚠️" if result.status == "skipped" else "❌")
        rc = "-" if result.return_code is None else str(result.return_code)
        print(f"{marker} {result.name}: {result.status.upper()} (code={rc})")

    print("-----------------------------------------------")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Epic 5 final verification checks.")
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip docker compose validation step.",
    )
    args = parser.parse_args()

    checks = build_checks(skip_docker=args.skip_docker)
    results = [run_check(check) for check in checks]
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())
