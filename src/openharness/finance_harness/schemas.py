"""Shared schemas for the finance harness."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FinanceTaskType(str, Enum):
    DOCUMENT_QA = "document_qa"
    METRIC_QUERY = "metric_query"
    VARIANCE_ANALYSIS = "variance_analysis"
    REPORT_SUMMARY = "report_summary"
    RECONCILIATION = "reconciliation"
    DATA_QUALITY_CHECK = "data_quality_check"


class RehearsalDecision(str, Enum):
    PROCEED = "PROCEED"
    UPDATE = "UPDATE"
    ASK = "ASK"
    REFUSE = "REFUSE"


class SourceReference(BaseModel):
    source_id: str
    file_name: str | None = None
    sheet: str | None = None
    page: int | None = None
    cell_range: str | None = None
    record_ids: list[str] = Field(default_factory=list)


class FinanceRequest(BaseModel):
    request_id: str
    user_id: str
    user_role: str
    task_type: FinanceTaskType
    query: str
    source_ids: list[str] = Field(default_factory=list)
    period: str | None = None
    entity: str | None = None
    currency: str | None = None
    output_format: str = "json"


class RehearsalResult(BaseModel):
    decision: RehearsalDecision
    reasons: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    approval_required: bool = False


class FinanceResponse(BaseModel):
    request_id: str
    status: str
    answer: str
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[SourceReference] = Field(default_factory=list)
    calculations: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rehearsal: RehearsalResult | None = None
