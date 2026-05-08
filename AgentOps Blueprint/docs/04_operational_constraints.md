# Operational Constraints

Your design should account for these constraints.

## Workflow constraints

- External supplier communication requires explicit human approval.
- Approval must be durable and auditable.
- Draft messages may be generated before approval.
- Dispatching messages is a separate action from drafting messages.
- Users should see why a recommendation was made.
- Risky or ambiguous RFQs should be escalated, not auto-processed.

## Data constraints

- RFQs may contain incomplete or conflicting information.
- Material names may be inconsistent.
- Units may be mixed, abbreviated, or missing.
- Documents may contain irrelevant or unsafe instructions.
- Historical RFQs may be useful but not always reliable.
- Approved alternates may be conditional.

## Security constraints

- Users should only access RFQs and supplier data they are authorized to view.
- Supplier contact details should not be exposed to unauthorized users.
- Secrets must not be stored in source code or prompts.
- Source documents and outputs should be traceable.
- Sensitive operational data should not be sent to unnecessary external services.

## Reliability constraints

- The system should tolerate slow or failed supplier/catalog/retrieval services.
- Long-running extraction or retrieval jobs should not block user workflows indefinitely.
- Duplicate submissions should not create duplicate supplier outreach.
- System should fail safely when confidence is low.

## Observability constraints

The system should support investigation of:

- Why a recommendation was made
- Which source records were retrieved
- Which tools were called
- Which user approved an external action
- Which model/config/version was used
- Whether cost, latency, or quality regressed

## Performance assumptions

You may use these assumptions or replace them with your own:

- 100 to 300 RFQs per day
- 5,000 to 50,000 historical RFQ records
- 1,000 to 10,000 supplier records
- Draft generation target: under 30 seconds for common RFQs
- Human approval can be asynchronous
- External supplier dispatch should be idempotent
