"""Reference document identifiers used by the reimbursement assistant."""

from enum import Enum


class ReferenceDocumentKey(str, Enum):
    """Known reimbursement documents shown in the reference workflow."""

    REIMBURSEMENT_MANUAL_COST_EXPENSE = (
        "reimbursement_manual_cost_expense"
    )
    CENTRALIZED_BUDGET_PROCESS = "centralized_budget_process"
    BUSINESS_ACTIVITY_FINANCE_MAPPING = (
        "business_activity_finance_mapping"
    )
    IT_BUSINESS_CASHFLOW_MAPPING = (
        "it_business_cashflow_mapping"
    )
    MATERIAL_REQUIREMENTS = "material_requirements"
    MATERIAL_STANDARD_TEMPLATES = "material_standard_templates"
    IMAGING_SCAN_GUIDE = "imaging_scan_guide"
    REIMBURSEMENT_SYSTEM_MANUAL = "reimbursement_system_manual"
