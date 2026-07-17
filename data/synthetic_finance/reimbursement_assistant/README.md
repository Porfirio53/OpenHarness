# Synthetic reimbursement-assistant data

This directory contains synthetic contracts and future test fixtures only.

Do not add company reimbursement documents, user attachments, invoices, account
numbers, credentials, screenshots, internal manuals, or production logs. Private
reference documents and rule packs must use approved local storage outside Git.

`acceptance/day1_2_e2e_cases.jsonl` is the Day 1–2 acceptance contract. Its
`implementation_status` remains `contract_only` until the deterministic runner is
implemented during Day 6–7. The contract-validation tests run immediately.

The Day 3–5 candidate rule packs live under
`configs/finance/reimbursement_assistant/rule_packs`. They contain structured,
reviewable requirements and source locators, but no original company manuals.
Candidate packs must stay in `review_required` until finance approval and the
publication validator pass.
