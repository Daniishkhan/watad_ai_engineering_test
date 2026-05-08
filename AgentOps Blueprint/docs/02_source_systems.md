# Source Systems and Integration Points

Use this as the assumed environment for your design. You may propose changes, but state the trade-offs.

## Input channels

### RFQ Inbox

Receives supplier and contractor RFQ emails with attachments.

Possible inputs:

- Email body
- PDF attachment
- Excel attachment
- Image or scanned document
- Free-text request from internal project team

### Internal RFQ Form

Structured form used by internal teams.

Common fields:

- requester_id
- project_id
- material_description
- quantity
- unit
- needed_by_date
- delivery_location
- supporting_document_refs
- preferred_supplier_ids

## Operational systems

### Supplier Master

Stores supplier identity, categories, approval status, regions, contact channels, and risk flags.

### Item Catalog

Stores normalized material names, SKUs, units, specification standards, and category mappings.

### Approved Alternates Registry

Stores approved substitute materials and constraints.

### Historical RFQ Store

Stores previous RFQs, selected suppliers, quoted prices, lead times, final outcomes, and notes.

### Procurement Workflow API

Backend API that stores RFQ state and manages workflow actions.

Example actions:

- create_rfq
- update_rfq_status
- attach_extracted_fields
- submit_for_human_review
- record_approval
- dispatch_supplier_message

### Notification Service

Sends internal notifications to procurement users.

External supplier communication must not happen unless approval status is approved.

## Observability systems

Assume the company can use:

- Application logs
- Structured events
- Traces
- Metrics dashboards
- LLM/agent traces
- Offline evaluation reports
- Regression test results

You may choose tools and explain why.

## Storage options

You may assume availability of:

- Postgres
- pgvector
- Redis
- Object storage for source files
- Queue or background job system

You may propose additional infrastructure only if justified.
