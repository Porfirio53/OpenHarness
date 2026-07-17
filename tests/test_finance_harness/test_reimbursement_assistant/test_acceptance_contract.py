"""Validation for the Day 1-2 end-to-end acceptance contract."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from openharness.finance_harness.reimbursement_assistant.reference_catalog import (
    ReferenceDocumentKey,
)
from openharness.finance_harness.reimbursement_assistant.schemas import (
    FlowDecision,
    ReimbursementBlockReason,
    ReimbursementStage,
)


ACCEPTANCE_PATH = (
    Path(__file__).parents[3]
    / "data"
    / "synthetic_finance"
    / "reimbursement_assistant"
    / "acceptance"
    / "day1_2_e2e_cases.jsonl"
)
SUPPORTED_SCENES = {"travel_domestic", "meeting_expense", "it_maintenance_support"}


def load_cases() -> list[dict[str, Any]]:
    """Load the synthetic case contract without importing future runtime code."""

    return [json.loads(line) for line in ACCEPTANCE_PATH.read_text(encoding="utf-8").splitlines()]


def test_acceptance_contract_contains_20_unique_synthetic_cases() -> None:
    cases = load_cases()
    case_ids = [case["case_id"] for case in cases]

    assert len(cases) == 20
    assert len(set(case_ids)) == len(case_ids)
    assert all(case_id.startswith("RA-E2E-") for case_id in case_ids)
    assert all(case["data_classification"] == "synthetic" for case in cases)


def test_acceptance_contract_covers_all_pilot_scenes_and_safe_fallbacks() -> None:
    cases = load_cases()
    counts = Counter(case["scene"] for case in cases)

    assert all(counts[scene] >= 4 for scene in SUPPORTED_SCENES)
    assert counts["unsupported"] >= 1
    assert counts["unknown"] >= 1


def test_acceptance_contract_uses_stable_enum_values_and_sources() -> None:
    cases = load_cases()
    decisions = {item.value for item in FlowDecision}
    stages = {item.value for item in ReimbursementStage}
    block_reasons = {item.value for item in ReimbursementBlockReason}
    reference_document_ids = {item.value for item in ReferenceDocumentKey}

    for case in cases:
        expected = case["expected"]
        assert expected["decision"] in decisions
        assert expected["stage"] in stages
        assert set(expected["block_reasons"]) <= block_reasons
        assert case["source_document_ids"]
        assert set(case["source_document_ids"]) <= reference_document_ids
        assert case["implementation_status"] == "contract_only"


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: str(case["case_id"]))
def test_future_acceptance_runner_has_a_complete_contract(case: dict[str, Any]) -> None:
    """Keep every Day 1-2 scenario visible until the Day 6-7 runner is implemented."""

    required_expected_keys = {"decision", "stage", "block_reasons", "missing_items"}

    assert case["messages"]
    assert required_expected_keys <= set(case["expected"])
    assert isinstance(case["facts"], dict)
