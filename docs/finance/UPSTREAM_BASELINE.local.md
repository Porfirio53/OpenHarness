# Local OpenHarness baseline

Captured at: `2026-07-17T09:34:18+08:00`

Platform: `Linux 6.18.33.2-microsoft-standard-WSL2`

This file contains tool versions and bounded command output only. It intentionally does not capture environment variables, usernames, hostnames, or business documents.

## Source and toolchain

### `git branch --show-current`

Exit code: `0`

```text
feature/reimbursement-assistant-bootstrap
```

### `git rev-parse HEAD`

Exit code: `0`

```text
b862b1a894a7d1c1f7f0160da558aea866099c8d
```

### `git status --short`

Exit code: `0`

```text
M .gitignore
 M configs/finance/reimbursement_assistant.example.yaml
 M data/synthetic_finance/reimbursement_assistant/README.md
 M pyproject.toml
 M src/openharness/finance_harness/reimbursement_assistant/reference_catalog.py
 M src/openharness/finance_harness/reimbursement_assistant/schemas.py
 M tests/test_finance_harness/test_reimbursement_assistant/test_schemas.py
?? data/synthetic_finance/reimbursement_assistant/acceptance/
?? docs/finance/DAY1_2_HANDOFF.md
?? docs/finance/REIMBURSEMENT_ASSISTANT_ACCEPTANCE.md
?? docs/finance/UPSTREAM_BASELINE.local.md
?? docs/finance/UPSTREAM_BASELINE.md
?? docs/finance/adr/
?? finance_harness_day1_2.patch
?? scripts/finance/
?? tests/test_finance_harness/test_reimbursement_assistant/test_acceptance_contract.py
```

### `python --version`

Exit code: `0`

```text
Python 3.11.15
```

### `uv --version`

Exit code: `0`

```text
uv 0.11.28 (x86_64-unknown-linux-gnu)
```

### `node --version`

Exit code: `0`

```text
v20.20.2
```

### `npm --version`

Exit code: `0`

```text
10.8.2
```

## Verification summary

All requested checks passed.

## Verification details

### `uv run --extra dev pytest -q tests/test_finance_harness/test_reimbursement_assistant`

Exit code: `0`

```text
..................................                                       [100%]
34 passed in 0.06s
```

### `uv run --extra dev ruff check src/openharness/finance_harness/reimbursement_assistant tests/test_finance_harness/test_reimbursement_assistant scripts/finance/capture_reimbursement_baseline.py`

Exit code: `0`

```text
All checks passed!
```

### `uv run --extra dev mypy src/openharness/finance_harness/reimbursement_assistant scripts/finance/capture_reimbursement_baseline.py`

Exit code: `0`

```text
Success: no issues found in 13 source files
```

### `uv run --extra dev pytest -q`

Exit code: `0`

```text
........................................................................ [  6%]
........................................................................ [ 12%]
........................................................................ [ 18%]
........................................................................ [ 24%]
........................................................................ [ 30%]
........................................................................ [ 36%]
........................................................................ [ 42%]
........................................................................ [ 48%]
........................................................................ [ 54%]
........................s............................................... [ 60%]
........................................................................ [ 66%]
........................................................................ [ 72%]
........................................................................ [ 78%]
........................................................................ [ 84%]
........................................................................ [ 90%]
.................................................................s...... [ 96%]
ss..ss.....................................                              [100%]
1189 passed, 6 skipped in 18.20s
```

### `npx tsc --noEmit`

Exit code: `0`

```text
(no output)
```
