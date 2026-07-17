"""Stable contracts for the reimbursement assistant workflow.

The models in this module deliberately contain no reimbursement rules.  They
define the boundary between deterministic rule evaluation, optional model
assistance, OpenHarness integration, and the audit trail.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReimbursementIntent(str, Enum):
    """Supported user intents defined by the reimbursement assistant scope."""

    SCENE_CLASSIFICATION = "scene_classification"
    PROCESS_GUIDANCE = "process_guidance"
    ATTACHMENT_CHECK = "attachment_check"
    FIELD_CHECK = "field_check"
    FORM_GUIDANCE = "form_guidance"
    ERROR_QA = "error_qa"
    TEMPLATE_FILL = "template_fill"


class ReimbursementStage(str, Enum):
    """Stages appearing in the reimbursement reference flow."""

    USER_NEED = "user_need"
    SCENE_CLASSIFICATION = "scene_classification"
    BUDGET_PROJECT_CONFIRMATION = "budget_project_confirmation"
    FUNDING_PLAN_CONFIRMATION = "funding_plan_confirmation"
    SUPPORTING_MATERIAL_CHECK = "supporting_material_check"
    FORM_FIELD_GUIDANCE = "form_field_guidance"
    ERROR_QA = "error_qa"
    TEMPLATE_FILL = "template_fill"
    COMPLETED = "completed"


class FlowDecision(str, Enum):
    """Control decision for the current reimbursement conversation."""

    CONTINUE = "CONTINUE"
    ASK_USER = "ASK_USER"
    STOP_AND_FEEDBACK = "STOP_AND_FEEDBACK"
    COMPLETE = "COMPLETE"


class ReimbursementBlockReason(str, Enum):
    """Stable reason codes for conservative stops and human escalation."""

    UNSUPPORTED_SCENE = "unsupported_scene"
    LOW_CLASSIFICATION_CONFIDENCE = "low_classification_confidence"
    MISSING_BUDGET_PROJECT = "missing_budget_project"
    MISSING_FUNDING_PLAN = "missing_funding_plan"
    MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
    UNREADABLE_EVIDENCE = "unreadable_evidence"
    SOURCE_CONFLICT = "source_conflict"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


class RulePackStatus(str, Enum):
    """Lifecycle states for immutable reimbursement rule packs."""

    CANDIDATE = "candidate"
    REVIEW_REQUIRED = "review_required"
    ACTIVE = "active"
    RETIRED = "retired"


class AuditEventType(str, Enum):
    """Events needed to reproduce a reimbursement assistant decision."""

    REQUEST_RECEIVED = "request_received"
    SCENE_CLASSIFIED = "scene_classified"
    GATE_EVALUATED = "gate_evaluated"
    RULE_EVALUATED = "rule_evaluated"
    HUMAN_REVIEW_REQUESTED = "human_review_requested"
    RESPONSE_RETURNED = "response_returned"


class AttachmentMedium(str, Enum):
    """Attachment categories shown in the reimbursement flow."""

    PAPER = "paper"
    ELECTRONIC = "electronic"


class AttachmentInput(BaseModel):
    """An attachment supplied by the user."""

    attachment_id: str
    file_name: str
    media_type: str | None = None
    medium: AttachmentMedium | None = None
    extracted_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessReference(BaseModel):
    """Traceable reference to a reimbursement guide or manual."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    title: str
    document_version: str | None = None
    effective_date: date | None = None
    section: str | None = None
    page: int | None = None
    table: str | None = None
    row: str | None = None
    locator: str | None = None
    content_checksum: str | None = None


class ConfidenceAssessment(BaseModel):
    """Explainable classification confidence and its configured threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list)

    @property
    def requires_clarification(self) -> bool:
        """Return whether the score is below the configured acceptance threshold."""

        return self.score < self.threshold


class RulePackVersion(BaseModel):
    """Identity of the exact immutable rule pack used for a response."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_pack_id: str
    scene_id: str
    version: str
    status: RulePackStatus
    content_checksum: str
    source_document_ids: list[str] = Field(default_factory=list)


class ReimbursementAuditEvent(BaseModel):
    """Redacted event sufficient for decision replay without business documents."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    conversation_id: str
    occurred_at: datetime
    event_type: AuditEventType
    stage: ReimbursementStage
    decision: FlowDecision | None = None
    rule_pack: RulePackVersion | None = None
    rule_ids: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    redacted_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Reject ambiguous timestamps so event ordering is reproducible."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value


class ChecklistResult(BaseModel):
    """Result of an attachment or field completeness check."""

    required_items: list[str] = Field(default_factory=list)
    present_items: list[str] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return not self.missing_items


class ReimbursementAssistantRequest(BaseModel):
    """Normalized input passed to the reimbursement assistant."""

    conversation_id: str
    request_id: str | None = None
    user_id: str
    message: str
    stage: ReimbursementStage = ReimbursementStage.USER_NEED
    scene: str | None = None
    budget_project_confirmed: bool | None = None
    funding_plan_confirmed: bool | None = None
    attachments: list[AttachmentInput] = Field(default_factory=list)
    form_fields: dict[str, Any] = Field(default_factory=dict)
    image_ids: list[str] = Field(default_factory=list)


class ReimbursementAssistantResponse(BaseModel):
    """Structured output returned by the reimbursement assistant."""

    conversation_id: str
    intent: ReimbursementIntent
    stage: ReimbursementStage
    decision: FlowDecision
    scene: str | None = None
    classification_confidence: ConfidenceAssessment | None = None
    block_reasons: list[ReimbursementBlockReason] = Field(default_factory=list)
    rule_pack: RulePackVersion | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    guidance: list[str] = Field(default_factory=list)
    next_question: str | None = None
    attachment_check: ChecklistResult | None = None
    field_check: ChecklistResult | None = None
    error_answer: str | None = None
    template_values: dict[str, Any] = Field(default_factory=dict)
    references: list[ProcessReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
