"""Reference document identifiers used by the reimbursement assistant."""

from enum import Enum


class ReferenceDocumentKey(str, Enum):
    """Known reimbursement documents shown in the reference workflow."""

    REIMBURSEMENT_ASSISTANT_MVP_SCOPE = "reimbursement_assistant_mvp_scope"
    REIMBURSEMENT_FLOW_REFERENCE = "reimbursement_flow_reference"
    REIMBURSEMENT_MANUAL_COST_EXPENSE = "reimbursement_manual_cost_expense"
    CENTRALIZED_BUDGET_PROCESS = "centralized_budget_process"
    BUDGET_YEAR_END_FAQ = "budget_year_end_faq"
    BUSINESS_SCENE_CATALOG = "business_scene_catalog"
    BUSINESS_ACTIVITY_FINANCE_MAPPING = "business_activity_finance_mapping"
    IT_BUSINESS_CASHFLOW_MAPPING = "it_business_cashflow_mapping"
    MATERIAL_REQUIREMENTS = "material_requirements"
    MATERIAL_STANDARD_TEMPLATES = "material_standard_templates"
    IMAGING_SCAN_GUIDE = "imaging_scan_guide"
    REIMBURSEMENT_SYSTEM_MANUAL = "reimbursement_system_manual"
