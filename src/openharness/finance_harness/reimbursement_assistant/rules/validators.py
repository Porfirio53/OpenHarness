"""Deterministic validation and evaluation for reimbursement rule packs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    ConditionExpression,
    ConditionOperator,
    RuleDefinition,
    ScenarioRulePack,
    SourceApprovalStatus,
    SourceManifest,
)
from ..schemas import (
    ProcessReference,
    RulePackStatus,
)


class RuleValidationReport(BaseModel):
    """Machine-readable validation result used by CI and human approval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    errors: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    publish_blockers: tuple[str, ...] = Field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """Return whether schema-independent integrity checks passed."""

        return not self.errors

    @property
    def is_publishable(self) -> bool:
        """Return whether the pack is safe to activate."""

        return self.is_valid and not self.publish_blockers


class RulePackValidationError(ValueError):
    """Raised when a rule pack cannot be loaded or activated safely."""


_MISSING = object()


def _resolve_fact(facts: Mapping[str, Any], path: str) -> Any:
    current: Any = facts
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def evaluate_condition(condition: ConditionExpression, facts: Mapping[str, Any]) -> bool:
    """Evaluate the allowlisted condition language without executing user code."""

    if condition.operator is ConditionOperator.ALL:
        return all(evaluate_condition(item, facts) for item in condition.operands)
    if condition.operator is ConditionOperator.ANY:
        return any(evaluate_condition(item, facts) for item in condition.operands)

    assert condition.fact is not None  # guaranteed by the Pydantic model
    actual = _resolve_fact(facts, condition.fact)
    if condition.operator is ConditionOperator.EXISTS:
        return (actual is not _MISSING) is condition.value
    if actual is _MISSING:
        return False
    if condition.operator is ConditionOperator.EQ:
        return bool(actual == condition.value)
    if condition.operator is ConditionOperator.IN:
        return bool(actual in condition.value)
    if condition.operator is ConditionOperator.GT:
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            return False
        return bool(actual > condition.value)
    raise AssertionError(f"unsupported validated operator: {condition.operator}")


def evaluate_applicable_rules(
    pack: ScenarioRulePack,
    facts: Mapping[str, Any],
) -> tuple[RuleDefinition, ...]:
    """Return rules whose applicability conditions match the structured facts."""

    return tuple(
        rule
        for rule in pack.rules
        if rule.applies_when is None or evaluate_condition(rule.applies_when, facts)
    )


def _validate_reference(
    reference: ProcessReference,
    manifest: SourceManifest,
) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []
    source = manifest.by_id().get(reference.document_id)
    if source is None:
        errors.append(f"unknown source document: {reference.document_id}")
        blockers.append(f"source {reference.document_id} is not in the manifest")
        return errors, warnings, blockers

    if reference.title != source.title:
        errors.append(f"source title mismatch for {reference.document_id}")
    if reference.document_version != source.version:
        errors.append(f"source version mismatch for {reference.document_id}")
    if reference.content_checksum != source.content_checksum:
        errors.append(f"source checksum mismatch for {reference.document_id}")
    if source.effective_date is not None and reference.effective_date != source.effective_date:
        errors.append(f"source effective_date mismatch for {reference.document_id}")
    if reference.locator is None and reference.table is None and reference.section is None:
        errors.append(f"source locator is missing for {reference.document_id}")

    if source.requires_effective_date and source.effective_date is None:
        blockers.append(f"source {reference.document_id} has no confirmed effective date")
    if source.approval_status is not SourceApprovalStatus.APPROVED:
        message = (
            f"source {reference.document_id} status is {source.approval_status.value}; "
            "finance approval is required"
        )
        warnings.append(message)
        blockers.append(message)
    return errors, warnings, blockers


def _canonical_rule(rule: RuleDefinition) -> str:
    return json.dumps(
        rule.model_dump(mode="json", exclude={"rule_id", "source_refs"}),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def validate_rule_pack(
    pack: ScenarioRulePack,
    manifest: SourceManifest,
) -> RuleValidationReport:
    """Validate provenance, conflicts, lifecycle, and publication readiness."""

    errors: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []

    seen_references: set[tuple[str, str | None, str | None, str | None]] = set()
    for reference in pack.source_references():
        key = (
            reference.document_id,
            reference.table,
            reference.row,
            reference.locator,
        )
        if key in seen_references:
            continue
        seen_references.add(key)
        ref_errors, ref_warnings, ref_blockers = _validate_reference(reference, manifest)
        errors.extend(ref_errors)
        warnings.extend(ref_warnings)
        blockers.extend(ref_blockers)

    conflicts: dict[str, str] = {}
    for rule in pack.rules:
        if rule.conflict_key is None:
            continue
        canonical = _canonical_rule(rule)
        previous = conflicts.get(rule.conflict_key)
        if previous is not None and previous != canonical:
            message = f"conflicting rules share conflict_key {rule.conflict_key}"
            errors.append(message)
            blockers.append(message)
        conflicts[rule.conflict_key] = canonical

    if pack.status is not RulePackStatus.ACTIVE:
        blockers.append(f"rule pack status is {pack.status.value}, not active")
    if pack.status is RulePackStatus.ACTIVE and pack.effective_date is None:
        message = "active rule pack requires an effective_date"
        errors.append(message)
        blockers.append(message)

    return RuleValidationReport(
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
        publish_blockers=tuple(dict.fromkeys(blockers)),
    )


def validate_rule_pack_set(packs: tuple[ScenarioRulePack, ...]) -> RuleValidationReport:
    """Detect duplicate versions and overlapping active packs across a directory."""

    errors: list[str] = []
    blockers: list[str] = []
    versions: set[tuple[str, str]] = set()
    active_by_scene: dict[str, int] = {}

    for pack in packs:
        version_key = (pack.scene_id, pack.version)
        if version_key in versions:
            errors.append(f"duplicate rule pack version: {pack.scene_id}@{pack.version}")
        versions.add(version_key)
        if pack.status is RulePackStatus.ACTIVE:
            active_by_scene[pack.scene_id] = active_by_scene.get(pack.scene_id, 0) + 1

    for scene_id, count in active_by_scene.items():
        if count > 1:
            message = f"multiple active rule packs for scene {scene_id}"
            errors.append(message)
            blockers.append(message)

    return RuleValidationReport(
        errors=tuple(errors),
        publish_blockers=tuple(blockers),
    )


def assert_publishable(report: RuleValidationReport) -> None:
    """Raise with stable diagnostics when activation would be unsafe."""

    if report.is_publishable:
        return
    messages = report.errors + report.publish_blockers
    raise RulePackValidationError("; ".join(dict.fromkeys(messages)))
