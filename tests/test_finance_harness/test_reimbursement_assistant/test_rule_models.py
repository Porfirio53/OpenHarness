"""Unit tests for the safe rule language and publication validators."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from openharness.finance_harness.reimbursement_assistant.rules import (
    ConditionExpression,
    RulePackLoadError,
    RulePackValidationError,
    assert_publishable,
    evaluate_condition,
    load_rule_pack,
    load_rule_packs,
    load_source_manifest,
    validate_rule_pack,
)


ROOT = Path(__file__).parents[3]
RULE_ROOT = ROOT / "configs" / "finance" / "reimbursement_assistant"
MANIFEST_PATH = RULE_ROOT / "source_manifest.yaml"
PACK_ROOT = RULE_ROOT / "rule_packs"


def test_condition_language_evaluates_only_allowlisted_operations() -> None:
    condition = ConditionExpression.model_validate(
        {
            "operator": "all",
            "operands": [
                {"operator": "eq", "fact": "scene", "value": "travel_domestic"},
                {"operator": "in", "fact": "it_domain", "value": ["B", "M"]},
                {"operator": "exists", "fact": "attachments.invoice", "value": True},
                {"operator": "gt", "fact": "amount", "value": 5000},
                {
                    "operator": "any",
                    "operands": [
                        {"operator": "eq", "fact": "approved", "value": True},
                        {"operator": "eq", "fact": "reviewed", "value": True},
                    ],
                },
            ],
        }
    )

    facts = {
        "scene": "travel_domestic",
        "it_domain": "B",
        "attachments": {"invoice": "invoice.pdf"},
        "amount": 5000.01,
        "approved": False,
        "reviewed": True,
    }
    assert evaluate_condition(condition, facts)
    assert not evaluate_condition(condition, {**facts, "amount": 5000})


def test_missing_fact_is_false_except_for_exists_false() -> None:
    equality = ConditionExpression(operator="eq", fact="missing", value=True)
    missing = ConditionExpression(operator="exists", fact="missing", value=False)

    assert not evaluate_condition(equality, {})
    assert evaluate_condition(missing, {})


@pytest.mark.parametrize(
    "payload",
    [
        {"operator": "python", "fact": "x", "value": "open('/etc/passwd')"},
        {"operator": "eq", "fact": "__class__.__mro__", "value": "x"},
        {"operator": "all", "operands": []},
        {"operator": "gt", "fact": "amount", "value": "5000"},
        {"operator": "exists", "fact": "invoice", "value": "yes"},
    ],
)
def test_condition_language_rejects_executable_or_ambiguous_shapes(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ConditionExpression.model_validate(payload)


def test_three_candidate_packs_load_with_immutable_versions_and_sources() -> None:
    manifest = load_source_manifest(MANIFEST_PATH)
    loaded = load_rule_packs(PACK_ROOT, manifest)

    assert {item.pack.scene_id for item in loaded} == {
        "travel_domestic",
        "meeting_expense",
        "it_maintenance_support",
    }
    assert sum(len(item.pack.rules) for item in loaded) == 28
    for item in loaded:
        assert item.validation.is_valid
        assert not item.validation.is_publishable
        assert item.version.content_checksum.startswith("sha256:")
        assert item.version.source_document_ids


def test_finance_review_blocks_publication_without_invalidating_candidates() -> None:
    manifest = load_source_manifest(MANIFEST_PATH)
    loaded = load_rule_pack(PACK_ROOT / "travel_domestic.yaml", manifest)

    assert loaded.validation.is_valid
    assert any("finance approval" in item for item in loaded.validation.publish_blockers)
    with pytest.raises(RulePackValidationError):
        assert_publishable(loaded.validation)


def test_conflicting_rules_block_publication() -> None:
    manifest = load_source_manifest(MANIFEST_PATH)
    pack = load_rule_pack(PACK_ROOT / "travel_domestic.yaml", manifest).pack
    first, second, *remaining = pack.rules
    conflicting_second = second.model_copy(update={"conflict_key": first.conflict_key})
    conflicted = pack.model_copy(update={"rules": (first, conflicting_second, *remaining)})

    report = validate_rule_pack(conflicted, manifest)

    assert not report.is_valid
    assert any("conflicting rules" in item for item in report.errors)
    with pytest.raises(RulePackValidationError):
        assert_publishable(report)


def test_source_checksum_mismatch_is_rejected() -> None:
    manifest = load_source_manifest(MANIFEST_PATH)
    pack = load_rule_pack(PACK_ROOT / "travel_domestic.yaml", manifest).pack
    first, *remaining = pack.rules
    bad_ref = first.source_refs[0].model_copy(
        update={"content_checksum": "sha256:" + "0" * 64}
    )
    bad_rule = first.model_copy(update={"source_refs": (bad_ref,)})
    bad_pack = pack.model_copy(update={"rules": (bad_rule, *remaining)})

    report = validate_rule_pack(bad_pack, manifest)

    assert not report.is_valid
    assert any("checksum mismatch" in item for item in report.errors)


def test_loader_uses_safe_yaml_and_rejects_custom_tags(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe.yaml"
    unsafe.write_text("!!python/object/apply:os.system ['echo unsafe']", encoding="utf-8")

    with pytest.raises(RulePackLoadError, match="invalid safe YAML"):
        load_source_manifest(unsafe)
