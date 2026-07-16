# Reimbursement Assistant Scope

## Goal

Build an OpenHarness-based assistant that guides users through the
company reimbursement process using reimbursement manuals, operating
instructions, material requirements, and system guides.

## Supported capabilities

1. Identify the reimbursement type and business scenario through
   multi-turn conversation.
2. Return the corresponding reimbursement process guidance.
3. Check the completeness of supporting attachments.
4. Check the completeness of reimbursement form fields.
5. Provide reimbursement form filling guidance from text or optional
   image input.
6. Answer basic reimbursement-system error questions.
7. Optionally populate reimbursement templates from user-provided
   fields.
8. Support Harness updates when new reimbursement scenarios and guides
   are introduced.

## Reference flow

1. User need
2. Business-scenario classification
3. Budget-project confirmation
4. Funding-plan confirmation
5. Supporting-material completeness check
6. Detailed field guidance
7. Reimbursement error Q&A

A missing budget project or funding plan terminates the current flow and
returns feedback to the user.

## Data policy

Only synthetic or anonymized data may be committed to the repository.
Company manuals, financial records, user attachments, screenshots, and
credentials must remain outside Git.
