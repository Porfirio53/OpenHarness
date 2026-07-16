from openharness.finance_harness.schemas import (
    FinanceRequest,
    FinanceTaskType,
)


def test_finance_request_schema() -> None:
    request = FinanceRequest(
        request_id="req-001",
        user_id="user-001",
        user_role="analyst",
        task_type=FinanceTaskType.DOCUMENT_QA,
        query="总结本季度费用变化",
    )

    assert request.task_type == FinanceTaskType.DOCUMENT_QA
    assert request.output_format == "json"
