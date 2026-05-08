# Case Context
## Procurement RFQ Agent

A procurement and project operations company wants to build an internal AI-assisted workflow for handling contractor and supplier RFQs.

The current workflow is slow because RFQs arrive through emails, PDFs, spreadsheets, and internal forms. Material names are inconsistent. Units are mixed. Supporting documents are sometimes missing. Supplier outreach is often delayed because procurement teams must manually normalize specifications, search historical RFQs, check approved alternates, and draft supplier messages.

The company wants an agent-assisted workflow that improves speed while keeping control, traceability, and human approval.

## Core users

### Procurement Specialist

Reviews incoming RFQs, validates required fields, checks suggested alternates, and approves supplier outreach drafts.

### Category Manager

Owns supplier category strategy, approved alternates, preferred suppliers, and escalation rules.

### Project Requester

Submits RFQs and supporting documents. May not know exact material specifications.

### Compliance or Operations Reviewer

Needs auditability, approval history, and evidence behind decisions.

### System Admin

Manages integrations, permissions, configuration, and observability.

## Target workflow

1. RFQ is submitted through email, internal form, or document upload.
2. System extracts and normalizes material specifications.
3. System checks whether required fields are present.
4. System retrieves related previous RFQs, supplier records, and approved alternates.
5. Agent proposes next action and supplier outreach draft.
6. Human user reviews the evidence and either approves, edits, rejects, or escalates.
7. Only after approval, the system may trigger external supplier communication.
8. System stores audit trail, traces, citations, and outcome metadata.

## Business goal

Reduce manual triage time while maintaining control over supplier communication, data access, quality, and operational risk.

## Critical rule

The agent must never perform irreversible external actions without human approval.
