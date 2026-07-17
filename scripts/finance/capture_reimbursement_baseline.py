"""Capture a reproducible, non-sensitive OpenHarness development baseline."""

from __future__ import annotations

import argparse
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shutil import which


MAX_OUTPUT_LINES = 120


@dataclass(frozen=True)
class CommandResult:
    """Serializable result of one baseline command."""

    command: str
    exit_code: int
    output: str


def run_command(command: list[str], cwd: Path) -> CommandResult:
    """Run a fixed command and retain a bounded output tail."""

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return CommandResult(" ".join(command), 127, "command not found")

    combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    lines = combined.splitlines()
    if len(lines) > MAX_OUTPUT_LINES:
        lines = [
            f"... {len(lines) - MAX_OUTPUT_LINES} earlier lines omitted ...",
            *lines[-MAX_OUTPUT_LINES:],
        ]
    return CommandResult(" ".join(command), completed.returncode, "\n".join(lines))


def find_repo_root(start: Path) -> Path:
    """Resolve and validate the current Git repository root."""

    result = run_command(["git", "rev-parse", "--show-toplevel"], start)
    if result.exit_code != 0 or not result.output:
        raise RuntimeError("run this script from inside the OpenHarness Git repository")
    return Path(result.output.splitlines()[-1]).resolve()


def format_result(result: CommandResult) -> str:
    """Render one command result as Markdown."""

    output = result.output or "(no output)"
    return f"### `{result.command}`\n\nExit code: `{result.exit_code}`\n\n```text\n{output}\n```\n"


def capture_metadata(repo_root: Path) -> list[CommandResult]:
    """Capture source and toolchain identity without environment variables."""

    commands = [
        ["git", "branch", "--show-current"],
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--short"],
        ["python", "--version"],
        ["uv", "--version"],
        ["node", "--version"],
        ["npm", "--version"],
    ]
    return [run_command(command, repo_root) for command in commands]


def capture_checks(repo_root: Path) -> list[CommandResult]:
    """Run the Day 1–2 quality gates in increasing scope."""

    commands = [
        [
            "uv",
            "run",
            "--extra",
            "dev",
            "pytest",
            "-q",
            "tests/test_finance_harness/test_reimbursement_assistant",
        ],
        [
            "uv",
            "run",
            "--extra",
            "dev",
            "ruff",
            "check",
            "src/openharness/finance_harness/reimbursement_assistant",
            "tests/test_finance_harness/test_reimbursement_assistant",
            "scripts/finance/capture_reimbursement_baseline.py",
        ],
        [
            "uv",
            "run",
            "--extra",
            "dev",
            "mypy",
            "src/openharness/finance_harness/reimbursement_assistant",
            "scripts/finance/capture_reimbursement_baseline.py",
        ],
        ["uv", "run", "--extra", "dev", "pytest", "-q"],
    ]
    results = [run_command(command, repo_root) for command in commands]

    frontend = repo_root / "frontend" / "terminal"
    if frontend.is_dir() and which("npx"):
        results.append(run_command(["npx", "tsc", "--noEmit"], frontend))
    else:
        results.append(CommandResult("npx tsc --noEmit", 127, "frontend or npx not found"))
    return results


def build_report(repo_root: Path, run_checks: bool) -> str:
    """Build the Markdown baseline report."""

    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
    metadata = capture_metadata(repo_root)
    checks = capture_checks(repo_root) if run_checks else []
    check_summary = (
        "All requested checks passed."
        if checks and all(result.exit_code == 0 for result in checks)
        else "One or more checks failed or were unavailable; inspect the command output."
        if checks
        else "Checks were not run. Re-run with `--run-checks`."
    )

    sections = [
        "# Local OpenHarness baseline\n",
        f"Captured at: `{captured_at}`\n",
        f"Platform: `{platform.system()} {platform.release()}`\n",
        "This file contains tool versions and bounded command output only. It intentionally "
        "does not capture environment variables, usernames, hostnames, or business documents.\n",
        "## Source and toolchain\n",
        *(format_result(result) for result in metadata),
        "## Verification summary\n",
        f"{check_summary}\n",
    ]
    if checks:
        sections.extend(
            ["## Verification details\n", *(format_result(result) for result in checks)]
        )
    return "\n".join(sections)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/finance/UPSTREAM_BASELINE.local.md"),
        help="report path relative to the repository root",
    )
    parser.add_argument(
        "--run-checks",
        action="store_true",
        help="run domain tests, static checks, full pytest, and frontend type checking",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path.cwd())
    output = args.output if args.output.is_absolute() else repo_root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(repo_root, bool(args.run_checks)), encoding="utf-8")
    print(f"baseline written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
