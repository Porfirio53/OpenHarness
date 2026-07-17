"""Safe, immutable models for reimbursement rule packs.

The condition language intentionally contains a very small allowlist.  Rule
files are data, never executable Python, so a finance reviewer can understand
the exact condition that produced a decision.
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..schemas import (
    ProcessReference,
    RulePackStatus,
)


_STABLE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*$")
_RULE_PACK_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*@[a-z0-9][a-z0-9_.-]*$")
_FACT_PATH_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_CHECKSUM_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ConditionOperator(str, Enum):
    """Allowlisted operators supported by the deterministic evaluator."""

    EQ = "eq"
    IN = "in"
    EXISTS = "exists"
    GT = "gt"
    ALL = "all"
    ANY = "any"


class RuleCategory(str, Enum):
    """Business surface affected by a rule."""

    ATTACHMENT = "attachment"
    FIELD = "field"
    CONSISTENCY = "consistency"
    CLASSIFICATION = "classification"


class RuleSeverity(str, Enum):
    """Conservative action expected when a matching rule is unsatisfied."""

    BLOCKING = "blocking"
    REVIEW = "review"
    WARNING = "warning"


class SourceApprovalStatus(str, Enum):
    """Human-governed lifecycle of a source document snapshot."""

    APPROVED = "approved"
    REVIEW_REQUIRED = "review_required"
    RETIRED = "retired"


class ConditionExpression(BaseModel):
    """A recursively composed expression over a structured fact dictionary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operator: ConditionOperator
    fact: str | None = None
    value: Any = None
    operands: tuple[ConditionExpression, ...] = Field(default_factory=tuple)

    @field_validator("fact")
    @classmethod
    def validate_fact_path(cls, value: str | None) -> str | None:
        """Permit dotted dictionary paths and reject executable expressions."""

        if value is not None and not _FACT_PATH_PATTERN.fullmatch(value):
            raise ValueError("fact must be a safe dotted identifier")
        return value

    @model_validator(mode="after")
    def validate_operator_shape(self) -> ConditionExpression:
        """Require the correct fields for leaf and compound operators."""

        if self.operator in {ConditionOperator.ALL, ConditionOperator.ANY}:
            if self.fact is not None or not self.operands:
                raise ValueError("all/any require operands and do not accept fact")
            return self

        if self.fact is None or self.operands:
            raise ValueError("leaf operators require fact and do not accept operands")
        if self.operator is ConditionOperator.IN and not isinstance(self.value, (list, tuple)):
            raise ValueError("in requires a list value")
        if self.operator is ConditionOperator.EXISTS and not isinstance(self.value, bool):
            raise ValueError("exists requires a boolean value")
        if self.operator is ConditionOperator.GT and (
            isinstance(self.value, bool) or not isinstance(self.value, (int, float))
        ):
            raise ValueError("gt requires a numeric value")
        return self


class SourceDocument(BaseModel):
    """Metadata for one external source snapshot; the document stays outside Git."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    effective_date: date | None = None
    approval_status: SourceApprovalStatus
    content_checksum: str
    locator_hint: str = Field(min_length=1)
    requires_effective_date: bool = False
    notes: str | None = None

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, value: str) -> str:
        if not _STABLE_ID_PATTERN.fullmatch(value):
            raise ValueError("document_id must be a stable lowercase identifier")
        return value

    @field_validator("content_checksum")
    @classmethod
    def validate_checksum(cls, value: str) -> str:
        if not _CHECKSUM_PATTERN.fullmatch(value):
            raise ValueError("content_checksum must be sha256:<64 lowercase hex chars>")
        return value

    @model_validator(mode="after")
    def validate_approval_metadata(self) -> SourceDocument:
        if (
            self.approval_status is SourceApprovalStatus.APPROVED
            and self.requires_effective_date
            and self.effective_date is None
        ):
            raise ValueError("approved policy sources require an effective_date")
        return self


class SourceManifest(BaseModel):
    """Versioned collection of allowed evidence sources."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    manifest_id: str
    version: str
    sources: tuple[SourceDocument, ...] = Field(min_length=1)

    @field_validator("manifest_id")
    @classmethod
    def validate_manifest_id(cls, value: str) -> str:
        if not _STABLE_ID_PATTERN.fullmatch(value):
            raise ValueError("manifest_id must be a stable lowercase identifier")
        return value

    @model_validator(mode="after")
    def require_unique_documents(self) -> SourceManifest:
        ids = [source.document_id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source manifest contains duplicate document_id values")
        return self

    def by_id(self) -> dict[str, SourceDocument]:
        """Return a lookup without exposing mutable manifest state."""

        return {source.document_id: source for source in self.sources}


class ClassificationPolicy(BaseModel):
    """Deterministic hints that constrain later model-assisted classification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    aliases: tuple[str, ...] = Field(min_length=1)
    positive_signals: tuple[str, ...] = Field(min_length=1)
    exclusion_signals: tuple[str, ...] = Field(default_factory=tuple)
    clarification_questions: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[ProcessReference, ...] = Field(min_length=1)


class GatePolicy(BaseModel):
    """A sourced prerequisite evaluated before supporting materials."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    required: bool = True
    missing_item: str
    user_message: str = Field(min_length=1)
    source_refs: tuple[ProcessReference, ...] = Field(min_length=1)

    @field_validator("missing_item")
    @classmethod
    def validate_missing_item(cls, value: str) -> str:
        if not _STABLE_ID_PATTERN.fullmatch(value):
            raise ValueError("missing_item must be a stable lowercase identifier")
        return value


class GateRequirements(BaseModel):
    """Budget and funding gates shared by every pilot scenario."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    budget_project: GatePolicy
    funding_plan: GatePolicy


class ProcessGuidance(BaseModel):
    """Sourced form path and summary guidance returned after preflight gates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    form_type: str = Field(min_length=1)
    paths: tuple[str, ...] = Field(min_length=1)
    summary_template: str = Field(min_length=1)
    source_refs: tuple[ProcessReference, ...] = Field(min_length=1)


class BusinessMapping(BaseModel):
    """One allowed business-major/minor/activity combination."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    business_major: str = Field(min_length=1)
    business_minor: str = Field(min_length=1)
    activities: tuple[str, ...] = Field(min_length=1)
    applies_when: ConditionExpression | None = None
    source_refs: tuple[ProcessReference, ...] = Field(min_length=1)


class RuleDefinition(BaseModel):
    """A sourced requirement activated by an optional deterministic condition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    category: RuleCategory
    description: str = Field(min_length=1)
    applies_when: ConditionExpression | None = None
    required_items: tuple[str, ...] = Field(min_length=1)
    severity: RuleSeverity
    user_message: str = Field(min_length=1)
    source_refs: tuple[ProcessReference, ...] = Field(min_length=1)
    conflict_key: str | None = None

    @field_validator("rule_id", "conflict_key")
    @classmethod
    def validate_stable_ids(cls, value: str | None) -> str | None:
        if value is not None and not _STABLE_ID_PATTERN.fullmatch(value):
            raise ValueError("rule identifiers must use lowercase stable IDs")
        return value

    @field_validator("required_items")
    @classmethod
    def validate_required_items(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("required_items must be unique within a rule")
        if any(not _STABLE_ID_PATTERN.fullmatch(value) for value in values):
            raise ValueError("required_items must use lowercase stable IDs")
        return values


class ScenarioRulePack(BaseModel):
    """An immutable, human-reviewed rule bundle for one reimbursement scene."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    rule_pack_id: str
    scene_id: str
    display_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: RulePackStatus
    effective_date: date | None = None
    data_classification: str = "internal_derived"
    boundary: str = Field(min_length=1)
    classification: ClassificationPolicy
    gates: GateRequirements
    process: ProcessGuidance
    business_mappings: tuple[BusinessMapping, ...] = Field(min_length=1)
    rules: tuple[RuleDefinition, ...] = Field(min_length=1)

    @field_validator("rule_pack_id")
    @classmethod
    def validate_rule_pack_id(cls, value: str) -> str:
        if not _RULE_PACK_ID_PATTERN.fullmatch(value):
            raise ValueError("rule_pack_id must use '<scene_id>@<version>'")
        return value

    @field_validator("scene_id")
    @classmethod
    def validate_scene_id(cls, value: str) -> str:
        if not _STABLE_ID_PATTERN.fullmatch(value):
            raise ValueError("scene_id must use a lowercase stable ID")
        return value

    @model_validator(mode="after")
    def validate_identity_and_rules(self) -> ScenarioRulePack:
        if not self.rule_pack_id.startswith(f"{self.scene_id}@"):
            raise ValueError("rule_pack_id must start with '<scene_id>@'")
        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("rule pack contains duplicate rule_id values")
        return self

    def source_references(self) -> tuple[ProcessReference, ...]:
        """Collect every declared source reference in deterministic order."""

        references: list[ProcessReference] = []
        references.extend(self.classification.source_refs)
        references.extend(self.gates.budget_project.source_refs)
        references.extend(self.gates.funding_plan.source_refs)
        references.extend(self.process.source_refs)
        for mapping in self.business_mappings:
            references.extend(mapping.source_refs)
        for rule in self.rules:
            references.extend(rule.source_refs)
        return tuple(references)

    def source_document_ids(self) -> tuple[str, ...]:
        """Return the stable, deduplicated document IDs used by this pack."""

        return tuple(dict.fromkeys(ref.document_id for ref in self.source_references()))
