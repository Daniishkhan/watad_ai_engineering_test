# Submission Template
## AgentOps Blueprint

Use this structure if helpful. You may use a different structure if it is clearer.

## 1. Executive summary

Explain the proposed system in 5 to 8 sentences.

Include:

- Main workflow
- Key components
- Human approval model
- Main production risks

## 2. Architecture

Provide either a diagram or structured component description.

Include:

- User interfaces or entry points
- API/backend services
- Agent orchestration layer
- Tool execution layer
- Retrieval/indexing layer
- Data stores
- Queues/background jobs
- Observability/evaluation systems
- External communication boundary

## 3. Workflow/state machine

Describe the main states.

Suggested states:

- received
- parsed
- normalized
- missing_info_detected
- retrieved_context
- draft_generated
- pending_human_review
- approved
- rejected
- dispatched
- failed
- archived

Include transition rules and failure transitions.

## 4. Agent and tool boundaries

Explain what belongs to:

- Deterministic code
- LLM/agent reasoning
- Retrieval
- Human decision
- External action

State which actions the LLM is not allowed to perform directly.

## 5. Retrieval strategy

Explain:

- What gets indexed
- How chunking or records are structured
- Metadata filters
- Hybrid search or vector search approach
- Citation behavior
- Low-confidence behavior
- How retrieval quality is measured

## 6. Data model sketch

Include key entities and important fields.

Suggested entities:

- RFQ
- RFQ document
- extracted field
- supplier
- item/material
- approved alternate
- retrieval result
- draft message
- approval event
- external dispatch event
- audit log
- evaluation run

## 7. API surface sketch

Define the main endpoints or service interfaces.

Examples:

- create RFQ
- upload document
- extract fields
- retrieve context
- generate draft
- submit for review
- approve/reject
- dispatch approved message
- get audit trail

Include request/response shape only where useful.

## 8. Security, approval, and audit controls

Explain:

- RBAC or permission model
- Human approval gate
- Audit log
- Secrets handling
- Data redaction or access boundaries
- Prompt injection or unsafe document handling

## 9. Evaluation and observability

Explain:

- Offline eval sets
- Regression tests
- Online monitoring
- Traces/logs/metrics
- Quality metrics
- Cost and latency metrics
- Debugging workflow

## 10. Reliability and failure handling

Explain:

- Retries
- Timeouts
- Idempotency
- Queue behavior
- Fallbacks
- Low-confidence behavior
- Duplicate prevention

## 11. Cost and latency trade-offs

Explain:

- Model selection strategy
- Caching
- Async processing
- Batch/offline processing
- When not to use an LLM

## 12. Assumptions and out-of-scope

State what you assumed.

State what you intentionally did not solve in this 2-hour design.

## 13. Open questions

List the top questions you would ask product, operations, security, or engineering before implementation.
