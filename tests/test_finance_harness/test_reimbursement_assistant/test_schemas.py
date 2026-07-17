"""Contract tests for reimbursement-assistant boundary models."""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from openharness.finance_harness.reimbursement_assistant.reference_catalog import (
    ReferenceDocumentKey,
)
from openharness.finance_harness.reimbursement_assistant.schemas import (
    AttachmentInput,
    AttachmentMedium,
    AuditEventType,
    ChecklistResult,
    ConfidenceAssessment,
    FlowDecision,
    ProcessReference,
    ReimbursementAssistantRequest,
    ReimbursementAssistantResponse,
    ReimbursementAuditEvent,
    ReimbursementBlockReason,
    ReimbursementIntent,
    ReimbursementStage,
    RulePackStatus,
    RulePackVersion,
)


def test_existing_request_contract_remains_backward_compatible() -> None:
    request = ReimbursementAssistantRequest(
        conversation_id="conv-demo",
        user_id="synthetic-user",
        message="我需要报销一次国内出差费用",
    )

    assert request.request_id is None
    assert request.stage is ReimbursementStage.USER_NEED
    assert request.attachments == []


def test_existing_attachment_contract_remains_backward_compatible() -> None:
    request = ReimbursementAssistantRequest(
        conversation_id="conversation-001",
        user_id="synthetic-user",
        message="我要报销一次业务活动费用",
        attachments=[
            AttachmentInput(
                attachment_id="attachment-001",
                file_name="synthetic-invoice.pdf",
                media_type="application/pdf",
                medium=AttachmentMedium.ELECTRONIC,
            )
        ],
    )

    assert request.attachments[0].medium is AttachmentMedium.ELECTRONIC


def test_checklist_is_complete_only_when_nothing_is_missing() -> None:
    complete = ChecklistResult(required_items=["invoice"], present_items=["invoice"])
    incomplete = ChecklistResult(required_items=["invoice"], missing_items=["invoice"])

    assert complete.is_complete
    assert not incomplete.is_complete


def test_confidence_requires_clarification_below_threshold() -> None:
    low = ConfidenceAssessment(score=0.79, threshold=0.8, signals=["提到出差"])
    accepted = ConfidenceAssessment(score=0.8, threshold=0.8)

    assert low.requires_clarification
    assert not accepted.requires_clarification


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_confidence_rejects_values_outside_unit_interval(score: float) -> None:
    with pytest.raises(ValidationError):
        ConfidenceAssessment(score=score)


def test_process_reference_can_locate_versioned_evidence() -> None:
    reference = ProcessReference(
        document_id="reimbursement_manual_cost_expense",
        title="报账手册（成本费用域分册）",
        document_version="2025V1",
        effective_date=date(2025, 1, 1),
        section="国内差旅费报销/报账材料要求",
        table="TABLE 4",
        row="R0005",
        content_checksum="sha256:synthetic-demo",
    )

    assert reference.document_version == "2025V1"
    assert reference.row == "R0005"


def test_response_records_block_reason_and_rule_pack() -> None:
    rule_pack = RulePackVersion(
        rule_pack_id="travel_domestic@2025v1",
        scene_id="travel_domestic",
        version="2025v1.0",
        status=RulePackStatus.ACTIVE,
        content_checksum="sha256:synthetic-demo",
        source_document_ids=["reimbursement_manual_cost_expense"],
    )
    response = ReimbursementAssistantResponse(
        conversation_id="conv-demo",
        intent=ReimbursementIntent.PROCESS_GUIDANCE,
        stage=ReimbursementStage.BUDGET_PROJECT_CONFIRMATION,
        decision=FlowDecision.STOP_AND_FEEDBACK,
        scene="travel_domestic",
        block_reasons=[ReimbursementBlockReason.MISSING_BUDGET_PROJECT],
        rule_pack=rule_pack,
    )

    assert response.block_reasons == [ReimbursementBlockReason.MISSING_BUDGET_PROJECT]
    assert response.rule_pack == rule_pack


def test_existing_feedback_response_and_reference_catalog_remain_supported() -> None:
    response = ReimbursementAssistantResponse(
        conversation_id="conversation-001",
        intent=ReimbursementIntent.PROCESS_GUIDANCE,
        stage=ReimbursementStage.BUDGET_PROJECT_CONFIRMATION,
        decision=FlowDecision.ASK_USER,
        next_question="该业务场景是否已有预算项目？",
    )

    assert response.next_question is not None
    assert (
        ReferenceDocumentKey.REIMBURSEMENT_SYSTEM_MANUAL.value
        == "reimbursement_system_manual"
    )


def test_audit_event_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        ReimbursementAuditEvent(
            event_id="event-demo",
            conversation_id="conv-demo",
            occurred_at=datetime(2026, 7, 16, 9, 0),
            event_type=AuditEventType.GATE_EVALUATED,
            stage=ReimbursementStage.BUDGET_PROJECT_CONFIRMATION,
        )


def test_audit_event_accepts_only_redacted_decision_metadata() -> None:
    event = ReimbursementAuditEvent(
        event_id="event-demo",
        conversation_id="conv-demo",
        occurred_at=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc),
        event_type=AuditEventType.GATE_EVALUATED,
        stage=ReimbursementStage.BUDGET_PROJECT_CONFIRMATION,
        decision=FlowDecision.STOP_AND_FEEDBACK,
        rule_ids=["gate.budget.required"],
        reason_codes=[ReimbursementBlockReason.MISSING_BUDGET_PROJECT.value],
        redacted_metadata={"budget_project_confirmed": False},
    )

    assert event.occurred_at.utcoffset() is not None
    assert event.redacted_metadata == {"budget_project_confirmed": False}
