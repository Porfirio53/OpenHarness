from openharness.finance_harness.reimbursement_assistant.reference_catalog import (
    ReferenceDocumentKey,
)
from openharness.finance_harness.reimbursement_assistant.schemas import (
    AttachmentInput,
    AttachmentMedium,
    ChecklistResult,
    FlowDecision,
    ReimbursementAssistantRequest,
    ReimbursementAssistantResponse,
    ReimbursementIntent,
    ReimbursementStage,
)


def test_reimbursement_request_defaults_to_user_need() -> None:
    request = ReimbursementAssistantRequest(
        conversation_id="conversation-001",
        user_id="user-001",
        message="我要报销一次业务活动费用",
        attachments=[
            AttachmentInput(
                attachment_id="attachment-001",
                file_name="invoice.pdf",
                media_type="application/pdf",
                medium=AttachmentMedium.ELECTRONIC,
            )
        ],
    )

    assert request.stage == ReimbursementStage.USER_NEED
    assert request.attachments[0].medium == AttachmentMedium.ELECTRONIC


def test_checklist_is_complete_only_without_missing_items() -> None:
    complete = ChecklistResult(
        required_items=["发票", "审批材料"],
        present_items=["发票", "审批材料"],
    )
    incomplete = ChecklistResult(
        required_items=["发票", "审批材料"],
        present_items=["发票"],
        missing_items=["审批材料"],
    )

    assert complete.is_complete is True
    assert incomplete.is_complete is False


def test_response_supports_flow_feedback() -> None:
    response = ReimbursementAssistantResponse(
        conversation_id="conversation-001",
        intent=ReimbursementIntent.PROCESS_GUIDANCE,
        stage=ReimbursementStage.BUDGET_PROJECT_CONFIRMATION,
        decision=FlowDecision.ASK_USER,
        next_question="该业务场景是否已有预算项目？",
    )

    assert response.decision == FlowDecision.ASK_USER
    assert response.next_question is not None


def test_reference_catalog_contains_system_manual() -> None:
    assert (
        ReferenceDocumentKey.REIMBURSEMENT_SYSTEM_MANUAL.value
        == "reimbursement_system_manual"
    )
