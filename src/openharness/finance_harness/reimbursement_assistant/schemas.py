"""Schemas for the reimbursement assistant workflow."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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

    document_id: str
    title: str
    section: str | None = None
    page: int | None = None
    locator: str | None = None


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
    guidance: list[str] = Field(default_factory=list)
    next_question: str | None = None
    attachment_check: ChecklistResult | None = None
    field_check: ChecklistResult | None = None
    error_answer: str | None = None
    template_values: dict[str, Any] = Field(default_factory=dict)
    references: list[ProcessReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
