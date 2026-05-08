# AgentOps Blueprint Submission

## 1. Executive Summary

The proposed system is a production RFQ workflow service that receives contractor and project-team RFQs from email, forms, and document uploads, then extracts, normalizes, validates, retrieves supporting context, drafts a supplier outreach message, and routes the work to a human reviewer before any external action can occur. The agent is not an autonomous sender; it is a controlled orchestration layer that proposes next actions and drafts messages while deterministic services enforce authorization, required fields, approval policy, idempotency, and audit logging. Retrieval combines item catalog records, approved alternates, supplier master data, and historical RFQs so procurement users can see the evidence behind recommendations. Risky cases such as missing fields, ambiguous material references, unit conflicts, unsafe embedded instructions, low-confidence retrieval, supplier API failures, and unauthorized access are escalated instead of auto-processed. The main production risks are untrusted document content, weak retrieval citations, accidental supplier outreach, data leakage across roles/projects, duplicate dispatch, and regressions after model or prompt changes. The design therefore places supplier communication behind a durable approval gate, separates draft generation from dispatch, and records every source, model/config version, tool call, approval event, and external action.

## 2. Architecture

```text
Email inbox / RFQ form / Upload
        |
        v
Intake API + AuthN/AuthZ
        |
        +--> Object storage for source files
        +--> Postgres RFQ workflow database
        |
        v
Ingestion queue
        |
        v
Document text extraction worker
        |
        v
Extraction + normalization service
        |
        v
Validation and policy engine
        |
        +--> Item catalog
        +--> Supplier master
        +--> Approved alternates registry
        +--> Historical RFQ store
        +--> Retrieval index: keyword + vector
        |
        v
Draft and recommendation service
        |
        v
Procurement review UI
        |
        +--> approve / edit / reject / escalate
        |
        v
Approval service + audit log
        |
        v
Dispatch queue and outbox
        |
        v
Supplier email or portal adapter
```

Core components:

- `Intake API`: accepts email-ingested RFQs, internal form submissions, and document uploads. It applies authentication, project/category authorization, deduplication keys, and source-file persistence.
- `Workflow database`: stores RFQ state, extracted fields, validation results, retrieval citations, draft messages, approvals, and dispatch outcomes.
- `Object storage`: stores original emails, PDFs, Excel files, screenshots, OCR output, and normalized text snapshots with immutable source references.
- `Ingestion queue`: decouples user-facing submission from slower OCR, parsing, retrieval, and draft generation work.
- `Extraction and normalization service`: extracts structured RFQ fields, normalizes units and material names, and marks uncertainty rather than forcing a false answer.
- `Validation and policy engine`: deterministic gate for required fields, unsafe instructions, conflict detection, approval requirements, authorization, and external-action eligibility.
- `Retrieval service`: searches item catalog, supplier master, approved alternates, and historical RFQs with citations and confidence signals.
- `Draft and recommendation service`: prepares internal summary, clarification questions, and supplier outreach draft, but cannot dispatch.
- `Review UI`: shows extracted fields, uncertainty, source snippets, retrieved records, risk flags, and editable draft text to a procurement specialist or category manager.
- `Approval service`: records explicit human approval as a durable event and checks that the approver has permission for the project, supplier category, region, and action.
- `Dispatch worker`: sends only approved supplier communication through an idempotent outbox pattern.
- `Observability and evaluation`: structured logs, traces, metrics, model/config versions, offline regression reports, and alerting.

External communication boundary:

- Drafting supplier text is allowed before approval.
- Dispatching supplier communication is a separate backend action.
- Dispatch is blocked unless the RFQ has an approved approval event, the dispatch payload matches the approved draft or approved edits, and the user/action passes authorization.

## 3. Workflow and State Machine

Main states:

| State | Meaning | Next transitions |
| --- | --- | --- |
| `received` | RFQ was submitted from email, form, or upload. | `parsed`, `failed` |
| `parsed` | Text and metadata were extracted from sources. | `normalized`, `missing_info_detected`, `failed` |
| `normalized` | Materials, quantities, units, dates, and locations were normalized where possible. | `retrieved_context`, `missing_info_detected`, `conflict_detected` |
| `missing_info_detected` | Required fields such as delivery date or location are missing. | `pending_human_review`, `archived` |
| `conflict_detected` | Source values conflict, such as meters in email and pieces in attachment. | `pending_human_review`, `escalated` |
| `retrieved_context` | Related suppliers, catalog items, historical RFQs, and alternates were retrieved. | `draft_generated`, `low_confidence_retrieval` |
| `low_confidence_retrieval` | Retrieval confidence is weak or citations are not trustworthy. | `pending_human_review`, `escalated` |
| `draft_generated` | A summary and supplier outreach draft were generated. | `pending_human_review` |
| `pending_human_review` | A human must approve, edit, reject, or escalate. | `approved`, `rejected`, `escalated` |
| `approved` | Authorized human approved the specific external action. | `dispatch_queued` |
| `rejected` | Human rejected the proposed action. | `archived` |
| `escalated` | Category manager, compliance, or operations reviewer must decide. | `pending_human_review`, `rejected`, `archived` |
| `dispatch_queued` | Approved message is queued for supplier communication. | `dispatched`, `failed` |
| `dispatched` | Supplier communication completed successfully. | `archived` |
| `failed` | A processing or integration error occurred. | `pending_human_review`, `dispatch_queued`, `archived` |
| `archived` | RFQ is closed or retained for audit/evaluation. | none |

Transition rules:

- `received -> parsed`: only after source file checks, virus scan if available, metadata capture, and source snapshot persistence.
- `parsed -> normalized`: only when text extraction completes or a fallback text body is available.
- `normalized -> missing_info_detected`: if required fields are absent or too uncertain for the category.
- `normalized -> conflict_detected`: if extracted values disagree across sources or units cannot be reconciled.
- `retrieved_context -> draft_generated`: only when retrieval has enough cited evidence to support the recommendation.
- `retrieved_context -> low_confidence_retrieval`: if search confidence is low, citations are irrelevant, or approved-alternate conditions are not satisfied.
- `draft_generated -> pending_human_review`: every external supplier draft requires review, even if the RFQ is clean.
- `pending_human_review -> approved`: only an authorized human can approve the exact action and payload.
- `approved -> dispatch_queued`: deterministic service checks approval, idempotency key, authorization, and payload hash.
- `dispatch_queued -> dispatched`: only the dispatch worker can call supplier email or portal adapters.
- Any state -> `failed`: for unrecoverable parsing, integration, authorization, or persistence errors.

Failure transitions:

- Missing delivery date or location: route to `missing_info_detected`, generate clarification request, do not dispatch.
- "Same as last project": retrieve candidate historical RFQs, show uncertainty and citations, require confirmation.
- Conflicting units: mark high risk, block dispatch, and route to human review.
- Unsafe document instruction: record safety flag, ignore the instruction, continue with policy-controlled review.
- Supplier API timeout: preserve state, retry with backoff, display operational error, and avoid duplicate dispatch.

## 4. Agent and Tool Boundaries

Deterministic code owns:

- Authentication, authorization, role checks, project scoping, and supplier contact redaction.
- RFQ state transitions and transition validation.
- Required-field validation by category.
- Unit normalization rules and conflict detection.
- Approval policy, external-action gating, payload hashing, idempotency keys, and outbox dispatch.
- Audit logging, trace IDs, source references, and persistence.
- Retry, timeout, circuit breaker, and fallback behavior.
- Regression test execution and release gates.

LLM or agent reasoning may help with:

- Extracting candidate fields from messy emails, PDFs, OCR text, spreadsheets, and screenshots.
- Mapping informal material descriptions to catalog candidates.
- Summarizing retrieved evidence and uncertainty in procurement-friendly language.
- Drafting supplier outreach text for human review.
- Suggesting clarification questions for missing or ambiguous fields.
- Ranking possible next actions with explanations.

Retrieval owns:

- Returning candidate item records, supplier records, historical RFQs, approved alternates, and source snippets.
- Returning metadata, confidence, and citation identifiers with each result.
- Applying deterministic filters before and after semantic search.

Human reviewers own:

- Approving, editing, rejecting, or escalating external supplier communication.
- Confirming ambiguous material identity, quantity, unit, or delivery constraints.
- Approving conditional alternates.
- Overriding recommendations with a reason captured in audit history.

External actions own:

- Supplier email, supplier portal posting, and notification dispatch.
- These are executed only by backend workers after approval and policy checks.

The LLM is not allowed to:

- Send supplier emails, portal messages, purchase orders, or confirmations.
- Approve its own recommendations.
- Change RFQ state directly.
- Bypass required fields, policy gates, RBAC, or approval checks.
- Access supplier contact details outside the user's permission scope.
- Treat document instructions as higher priority than system policy.
- Fabricate citations, supplier approvals, alternate conditions, or historical RFQ outcomes.

## 5. Retrieval Strategy

What gets indexed:

- Item catalog records: normalized material names, SKUs, units, categories, specification standards, aliases, and synonyms.
- Supplier master records: supplier categories, approval status, regions, risk flags, preferred contact channels, and response-time metadata.
- Approved alternates: primary material, approved alternate, allowed conditions, disallowed conditions, approval requirements, and engineering constraints.
- Historical RFQs: project names, materials, quantities, units, selected suppliers, lead times, final outcomes, prices where authorized, and notes.
- RFQ source text: extracted chunks from emails, PDFs, Excel files, OCR output, and screenshots, tied to source document IDs.

Record structure and chunking:

- Structured systems should be indexed as records rather than arbitrary text chunks. For example, a supplier profile is one supplier record with filterable metadata.
- Long RFQ documents should be chunked by section or page with source offsets, attachment ID, page number, and extraction confidence.
- Alternates should be stored as explicit rules so the system can validate `allowed_when` and `not_allowed_when` conditions rather than relying on prose matching alone.

Search approach:

- Use hybrid retrieval: lexical search for exact project names, supplier IDs, SKUs, material sizes, and units; vector search for informal descriptions such as "same as last Al Noor project."
- Apply metadata filters before ranking where possible: category, region, approved supplier status, project scope, user authorization, and active/inactive records.
- Re-rank results with deterministic rules for exact spec matches, valid supplier approval status, matching region, and explicit alternate constraints.
- For "same as last project," search historical RFQs by project alias and category, then show the top candidates and uncertainty instead of silently selecting one.

Citation behavior:

- Every recommendation must cite record IDs such as `RFQ-11892`, `SUP-2048`, or `ALT-774`.
- Drafts should include internal citations for reviewers, not for external supplier messages.
- If a cited record is no longer authorized for the reviewer, the UI should show a redacted reason rather than leaking details.
- If the retrieval result does not support the recommendation, the recommendation should be blocked or downgraded to a clarification request.

Low-confidence behavior:

- Do not fabricate citations.
- Fall back from vector search to keyword search and deterministic catalog lookup.
- If still weak, route to human review with "retrieval_gap" and the attempted queries.
- For alternates, require explicit condition match and human approval even when retrieval confidence is high.

Retrieval quality measurement:

- Citation precision at top 3 and top 5.
- Material match accuracy against labeled RFQ examples.
- Supplier eligibility accuracy by region, category, and approval status.
- Approved-alternate condition accuracy.
- Human acceptance rate of retrieved evidence.
- Rate of retrieval gaps and irrelevant citations.
- Regression checks after index, prompt, embedding, or model changes.

## 6. Data Model Sketch

Key entities:

| Entity | Important fields |
| --- | --- |
| `rfq` | `id`, `source_channel`, `requester_id`, `project_id`, `current_state`, `risk_level`, `created_at`, `updated_at`, `dedupe_key` |
| `rfq_document` | `id`, `rfq_id`, `source_type`, `object_uri`, `text_snapshot_uri`, `checksum`, `page_count`, `ocr_confidence`, `received_at` |
| `extracted_field` | `id`, `rfq_id`, `field_name`, `value`, `normalized_value`, `unit`, `confidence`, `source_document_id`, `source_span`, `status` |
| `validation_result` | `id`, `rfq_id`, `missing_fields`, `conflicts`, `safety_flags`, `policy_version`, `created_at` |
| `supplier` | `supplier_id`, `name`, `categories`, `regions`, `approved`, `risk_flags`, `preferred_contact`, `contact_ref` |
| `item` | `item_id`, `normalized_name`, `aliases`, `category`, `standard_unit`, `specification_fields`, `active` |
| `approved_alternate` | `alternate_id`, `primary_item_id`, `alternate_item_id`, `allowed_when`, `not_allowed_when`, `approval_required`, `effective_dates` |
| `historical_rfq` | `rfq_id`, `project`, `material`, `quantity`, `unit`, `selected_supplier_id`, `lead_time_days`, `outcome`, `notes_ref` |
| `retrieval_result` | `id`, `rfq_id`, `record_type`, `record_id`, `score`, `reason`, `citation`, `retrieval_version`, `authorized_for_user` |
| `draft_message` | `id`, `rfq_id`, `channel`, `recipient_supplier_ids`, `body`, `source_citations`, `payload_hash`, `created_by`, `created_at` |
| `approval_event` | `id`, `rfq_id`, `draft_message_id`, `approver_id`, `decision`, `reason`, `approved_payload_hash`, `approved_at`, `approval_policy_version` |
| `dispatch_event` | `id`, `rfq_id`, `approval_event_id`, `supplier_id`, `channel`, `idempotency_key`, `status`, `attempt_count`, `external_message_id`, `sent_at` |
| `audit_log` | `id`, `actor_type`, `actor_id`, `rfq_id`, `action`, `before_state`, `after_state`, `metadata`, `trace_id`, `created_at` |
| `evaluation_run` | `id`, `dataset_version`, `model_version`, `prompt_version`, `policy_version`, `metrics`, `created_at`, `release_decision` |

## 7. API Surface Sketch

Representative endpoints:

### Create RFQ

```http
POST /rfqs
```

```json
{
  "source_channel": "internal_form",
  "requester_id": "USR-1004",
  "project_id": "PRJ-RIYADH-NORTH",
  "material_description": "galvanized steel pipe, 2 inch, medium class",
  "quantity": 2400,
  "unit": "meter",
  "needed_by_date": "2026-07-15",
  "delivery_location": "Site Gate B",
  "supporting_document_refs": ["OBJ-991"]
}
```

Returns:

```json
{
  "rfq_id": "RFQ-2026-00041",
  "state": "received",
  "trace_id": "trc_abc123"
}
```

### Upload Document

```http
POST /rfqs/{rfq_id}/documents
```

Stores the source file, checksum, metadata, and extraction job reference.

### Extract Fields

```http
POST /rfqs/{rfq_id}/extract
```

Runs extraction and normalization asynchronously, then writes `extracted_field` records and validation results.

### Retrieve Context

```http
POST /rfqs/{rfq_id}/retrieve-context
```

```json
{
  "include": ["items", "suppliers", "approved_alternates", "historical_rfqs"],
  "max_results_per_type": 5
}
```

Returns cited records with scores, reasons, and redaction flags.

### Generate Draft

```http
POST /rfqs/{rfq_id}/drafts
```

Creates an internal summary and supplier outreach draft for review. It does not dispatch.

### Submit for Review

```http
POST /rfqs/{rfq_id}/review
```

Moves the RFQ to `pending_human_review` with the current evidence package.

### Approve or Reject

```http
POST /rfqs/{rfq_id}/approvals
```

```json
{
  "draft_message_id": "DRF-9001",
  "decision": "approved",
  "reason": "Fields verified against source documents and supplier category is approved."
}
```

The backend stores approver identity, permission checks, decision, reason, policy version, and approved payload hash.

### Dispatch Approved Message

```http
POST /rfqs/{rfq_id}/dispatch
```

```json
{
  "approval_event_id": "APP-4407",
  "draft_message_id": "DRF-9001",
  "idempotency_key": "RFQ-2026-00041:DRF-9001:APP-4407"
}
```

The service rejects the call if the approval is missing, expired, unauthorized, or does not match the draft payload hash.

### Audit Trail

```http
GET /rfqs/{rfq_id}/audit
```

Returns source events, state transitions, retrieved citations, model/config versions, approval events, and dispatch attempts visible to the requesting user.

## 8. Security, Approval, and Audit Controls

RBAC and permissions:

- Procurement specialists can view and process RFQs for assigned projects/categories.
- Category managers can approve alternates, manage category escalation rules, and review high-risk supplier recommendations.
- Project requesters can view their own submissions and respond to clarification requests, but cannot see restricted supplier contacts unless authorized.
- Compliance and operations reviewers can view audit history according to scope.
- System admins manage configuration and integrations but should not bypass approval policy.

Human approval model:

- External supplier communication always requires explicit approval.
- Approval is durable: approver ID, timestamp, decision, reason, policy version, draft ID, and approved payload hash are stored.
- Dispatch is impossible unless a valid approval event exists for the exact payload.
- Editing a draft after approval invalidates the approval and sends it back to review.
- High-risk cases can require category manager or two-person approval.

Audit controls:

- Use append-only audit events for state transitions, tool calls, retrieval results, approval decisions, dispatch attempts, and policy violations.
- Link every generated draft to source document IDs, retrieval citations, prompt/model/config versions, and validation results.
- Preserve original source files and text snapshots with checksums.
- Emit trace IDs across intake, extraction, retrieval, review, and dispatch.

Secrets and data boundaries:

- Store API credentials in a secrets manager, not source code, prompts, or logs.
- Supplier contact details are stored as protected references and resolved only inside authorized dispatch or UI contexts.
- Redact sensitive supplier and pricing data from logs and model inputs unless needed and authorized.
- Apply project and region scoping before retrieval so the model never receives unauthorized records.
- Use egress controls or allowlists for model and messaging integrations.

Prompt injection and unsafe content:

- Treat emails, PDFs, spreadsheets, screenshots, and OCR text as untrusted data.
- Instructions inside source documents cannot override system policy.
- The policy engine blocks attempts to bypass approval, force supplier selection, confirm an order, or ignore missing fields.
- Unsafe instructions become safety flags visible in the review UI and audit log.

## 9. Evaluation and Observability

Offline evaluation:

- Build a labeled eval set from clean RFQs, messy requests, unsafe embedded instructions, missing fields, conflicting units, low-confidence retrieval, supplier timeouts, and unauthorized access attempts.
- Evaluate extraction accuracy for material, quantity, unit, delivery date, delivery location, project, requester, and supporting document references.
- Evaluate retrieval quality using expected citations for item catalog, suppliers, alternates, and historical RFQs.
- Evaluate policy behavior with hard assertions: unsafe instructions never dispatch, missing fields require review, low-confidence retrieval does not fabricate citations, and alternates require approval.
- Run regression tests before model, prompt, retrieval index, or policy changes are released.

Online observability:

- Logs: structured events for RFQ state changes, validation failures, safety flags, authorization decisions, approval events, and dispatch outcomes.
- Traces: end-to-end trace from intake through extraction, retrieval, draft generation, review, approval, and dispatch.
- Metrics: RFQs by state, missing-field rate, conflict rate, retrieval-gap rate, draft acceptance rate, approval latency, dispatch success/failure rate, duplicate prevention count, and unauthorized access denials.
- Quality metrics: extraction precision/recall, citation precision, human edit distance on drafts, alternate recommendation acceptance, and escalation rate.
- Cost and latency metrics: model tokens/cost per RFQ, retrieval latency, OCR latency, draft generation latency, queue age, and p95 time to review-ready package.
- Debugging workflow: select an RFQ, inspect source snapshots, extracted fields, retrieved records, policy decisions, model/config versions, and approval trail in one trace view.

Release controls:

- Pin model, prompt, retrieval, and policy versions.
- Use canary releases for new extraction/drafting configs.
- Block release if regression tests show external-action policy failures or alternate recommendation regressions.
- Keep rollback path to the previous config/index/model.

## 10. Reliability and Failure Handling

Retries and timeouts:

- Use timeouts on OCR, supplier master, item catalog, retrieval, workflow API, and dispatch adapters.
- Retry transient failures with exponential backoff and jitter.
- Use circuit breakers when a dependency is degraded.
- Route long-running extraction and retrieval to background jobs so the UI is not blocked indefinitely.

Idempotency and duplicate prevention:

- Compute a dedupe key from source channel, sender/requester, project, attachment checksum, subject, and received timestamp bucket.
- Use idempotency keys for RFQ creation, approval submission, and dispatch.
- Use an outbox table for supplier messages so a retry cannot send duplicates.
- Dispatch payload hash must match the approved draft hash.

Fallbacks:

- If vector retrieval fails, use keyword search and deterministic catalog lookup.
- If supplier master is unavailable, show a retryable operational error and keep the RFQ out of dispatch.
- If OCR confidence is low, request a better document or route to human review.
- If the model returns invalid structured output, retry once with a stricter schema prompt, then route to review with extraction failure details.
- If notification service fails for internal alerts, preserve the review task in the workflow database and retry notification.

Low-confidence behavior:

- Fail safe into human review.
- Show uncertainty and attempted retrieval queries.
- Do not generate supplier-facing claims that are not supported by cited records.
- Do not recommend alternates unless conditions are explicitly satisfied and a human approves.

## 11. Cost and Latency Trade-offs

Model strategy:

- Use deterministic code for auth, validation, state transitions, policy, and dispatch.
- Use smaller, cheaper extraction models or rules for simple form submissions.
- Use a stronger model only for messy unstructured text, screenshots after OCR, and complex draft summaries.
- Avoid LLM calls entirely when structured form fields are complete and only deterministic validation is needed.

Caching:

- Cache item catalog lookups, supplier eligibility checks, and common historical RFQ retrieval results.
- Cache embeddings for source documents and indexed records.
- Reuse extraction results when source file checksums match.

Async processing:

- Intake should return quickly with `received`.
- Extraction, retrieval, and drafting can run asynchronously, with the UI showing processing state.
- Human approval is naturally asynchronous, so draft generation does not need to block external dispatch.

Cost controls:

- Token budgets by RFQ type and risk level.
- Prompt and context trimming with cited records only.
- Batch embedding updates for historical RFQs and catalog changes.
- Alerts for cost per RFQ, model error rate, and retries.

Latency targets:

- Common structured RFQ to review-ready draft: under 30 seconds.
- Clean internal form without attachments: a few seconds.
- OCR-heavy or messy attachment cases: asynchronous, visible queue status, and no hidden auto-dispatch.

## 12. Assumptions and Out-of-Scope

Assumptions:

- The company has or can expose the source systems listed in the package: Supplier Master, Item Catalog, Approved Alternates Registry, Historical RFQ Store, Procurement Workflow API, Notification Service, Postgres, object storage, Redis, and a queue.
- Identity and role data are available from an internal identity provider.
- Email and supplier portal integrations can support idempotency keys or external message IDs.
- Historical RFQs have enough quality to be useful but not enough to be trusted without citation and review.
- Human approval can be asynchronous.
- External supplier communication includes email and portal messages, not purchase-order creation.

Out-of-scope for this design:

- Autonomous supplier negotiation.
- Automatic purchase order creation.
- Payment, invoicing, or contract execution.
- Full ERP replacement.
- Real-time chat support.
- Pricing optimization beyond citing historical RFQs.
- Legal review of supplier terms.
- Building a runnable implementation for this assessment.

## 13. Open Questions

- What are the required fields by RFQ category, project type, region, and supplier channel?
- Which roles can approve supplier outreach, alternates, high-risk suppliers, and edited drafts?
- Which categories require category manager review even when fields are complete?
- How should the system define and detect high-risk RFQs?
- What supplier communication channels are in scope: email, portal, ERP, or all three?
- Are supplier contacts and pricing records restricted by region, project, client, or category?
- What are the data residency and retention requirements for source documents and traces?
- Which OCR and document formats must be supported in the first release?
- How reliable is the item catalog, and who owns material alias cleanup?
- How much historical RFQ data is clean enough for retrieval and evaluation?
- What model hosting and vendor constraints apply to sensitive operational data?
- What is the acceptable cost per processed RFQ?
- What is the rollout plan: shadow mode, internal pilot, limited categories, then broader release?

## Failure Case Coverage Summary

| Failure case | System behavior |
| --- | --- |
| Missing delivery date or location | Mark missing fields, block dispatch, ask requester or route to human review. |
| "Same as last project" | Retrieve likely historical RFQs, show citations and uncertainty, require human confirmation. |
| Conflicting units | Mark high risk, preserve both source values, block dispatch, require review. |
| Unsafe document instruction | Treat as untrusted content, ignore policy-conflicting instruction, log safety flag, require approval. |
| Retrieval failure | Do not fabricate citations, fallback to keyword/catalog lookup, then human review if weak. |
| Supplier API timeout | Preserve RFQ state, retry safely, surface operational error, prevent duplicate dispatch. |
| Unauthorized user | Deny or redact data, log authorization event, never leak supplier contact details. |
| Prompt/model regression | Offline evals and online monitoring catch regression; config pinning and rollback restore prior behavior. |
