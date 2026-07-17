"""Behavior tests for every key condition and exception in the pilot packs."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from openharness.finance_harness.reimbursement_assistant.rules import (
    ScenarioRulePack,
    evaluate_applicable_rules,
    load_rule_packs,
    load_source_manifest,
)


ROOT = Path(__file__).parents[3]
RULE_ROOT = ROOT / "configs" / "finance" / "reimbursement_assistant"
MANIFEST = load_source_manifest(RULE_ROOT / "source_manifest.yaml")
PACKS = {
    item.pack.scene_id: item.pack
    for item in load_rule_packs(RULE_ROOT / "rule_packs", MANIFEST)
}


def matching_rule_ids(pack: ScenarioRulePack, facts: Mapping[str, Any]) -> set[str]:
    return {rule.rule_id for rule in evaluate_applicable_rules(pack, facts)}


@pytest.mark.parametrize(
    ("facts", "expected", "excluded"),
    [
        (
            {"third_party_taxi": True, "invoice_has_route_note": False},
            {"travel.taxi.itinerary.required"},
            set(),
        ),
        (
            {"third_party_taxi": True, "invoice_has_route_note": True},
            set(),
            {"travel.taxi.itinerary.required"},
        ),
        (
            {"hotel_non_centralized": True},
            {"travel.hotel.non_centralized.details.required"},
            set(),
        ),
        (
            {"itinerary_matches_application": False},
            {"travel.itinerary.change.explanation.required"},
            set(),
        ),
        (
            {"private_detour": True, "cross_period_claim": True},
            {"travel.private.detour.comparison.required", "travel.cross_period.approval.required"},
            set(),
        ),
        (
            {"platform_application": True, "centralized_settlement": True},
            set(),
            {"travel.application.offline.required", "travel.invoice.non_centralized.required"},
        ),
    ],
)
def test_travel_conditions_and_exceptions(
    facts: dict[str, object], expected: set[str], excluded: set[str]
) -> None:
    matched = matching_rule_ids(PACKS["travel_domestic"], facts)
    assert expected <= matched
    assert excluded.isdisjoint(matched)


def test_meeting_internal_and_external_material_branches() -> None:
    pack = PACKS["meeting_expense"]
    internal = matching_rule_ids(pack, {"external_meeting": False})
    external = matching_rule_ids(pack, {"external_meeting": True})

    assert "meeting.internal.preapproval.required" in internal
    assert "meeting.internal.attendance.required" in internal
    assert "meeting.external.material.exception" not in internal
    assert "meeting.external.material.exception" in external
    assert "meeting.internal.preapproval.required" not in external
    assert "meeting.internal.attendance.required" not in external


def test_meeting_hotel_advance_headcount_and_invoice_conditions() -> None:
    pack = PACKS["meeting_expense"]
    matched = matching_rule_ids(
        pack,
        {
            "external_meeting": False,
            "hotel_expense_incurred": True,
            "personal_advance_amount": 5000.01,
            "headcount_matches": False,
            "multiple_service_types": True,
            "invoice_tax_items_split": False,
        },
    )

    assert {
        "meeting.hotel.list.required",
        "meeting.personal.advance.payment.required",
        "meeting.headcount.difference.explanation",
        "meeting.invoice.tax.items.split",
    } <= matched
    at_threshold = matching_rule_ids(pack, {"personal_advance_amount": 5000})
    assert "meeting.personal.advance.payment.required" not in at_threshold


def test_it_formal_mode_and_domain_clarification() -> None:
    pack = PACKS["it_maintenance_support"]
    formal = matching_rule_ids(pack, {"reporting_mode": "formal", "it_domain": "B"})
    unsupported = matching_rule_ids(pack, {"reporting_mode": "accrual"})

    assert {
        "it.invoice.required",
        "it.contract.order.required",
        "it.signed.settlement.required",
    } <= formal
    assert "it.domain.clarification.required" not in formal
    assert "it.reporting.mode.formal.only" in unsupported
    assert "it.domain.clarification.required" in unsupported
    assert "it.invoice.required" not in unsupported


def test_it_contract_amount_account_and_order_conditions() -> None:
    pack = PACKS["it_maintenance_support"]
    matched = matching_rule_ids(
        pack,
        {
            "contract_additional_evidence_required": True,
            "settlement_information_complete": False,
            "order_contract_terms_consistent": False,
            "amounts_consistent": False,
            "contract_account_matches": False,
        },
    )

    assert {
        "it.contract.evidence.conditional",
        "it.settlement.information.complete",
        "it.order.contract.consistent",
        "it.amounts.consistent",
        "it.payment.account.consistent",
    } <= matched


def test_every_hard_requirement_has_precise_source_location() -> None:
    for pack in PACKS.values():
        for rule in pack.rules:
            assert rule.source_refs
            for reference in rule.source_refs:
                assert reference.content_checksum
                assert reference.document_version
                assert reference.section or reference.table or reference.locator
