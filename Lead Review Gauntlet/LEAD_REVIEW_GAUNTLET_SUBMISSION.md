# Lead Review Gauntlet - Submission

Candidate name: Danish Khan

Date: 2026-05-08

## 1. Review summary

The proposed assistant is directionally useful as an internal triage aid, but it is not safe enough for an internal pilot in its current form. The main issue is that the design and code let untrusted LLM output decide whether to send external email, even though the product requirement says external messages require correct approval and auditability. The implementation has no authentication, authorization, human approval workflow, durable audit log, or safe handling for credit-sensitive data. It also fails open in several places: missing retrieval guidance tells the model to use best judgment, model and email errors are swallowed, and the API returns a success-like response even when dependencies fail. The tests only check that response keys exist, so they would not catch unsafe sending, prompt-injection attempts, missing required fields, or service failure behavior. I recommend revising before approval, with the first pilot limited to draft-only recommendations until authorization, approval, audit, and safety tests are in place.

## 2. Final decision

Decision: Revise before approval

Rationale: The current design should not be piloted because it can perform externally visible actions without a trusted approval gate, and it does not meet the stated requirements for traceability, authorization, sensitive data handling, or safe failure. The underlying feature is worth continuing, but the next version must make the model advisory only and move approval, sending, and audit decisions into deterministic server-side policy.

## 3. Blocking issues

| Priority | Area | Issue | Impact | Recommended fix | Acceptance check |
|---|---|---|---|---|---|
| P0 | Design/Code/Safety | The LLM can trigger external email by emitting `SEND_EMAIL=true` and a confidence string. | A prompt-injected or mistaken model response could contact a supplier or applicant without approved human action. This directly conflicts with the requirement that external messages require correct approval. | Remove automatic sending from `/assist`. Make the endpoint produce drafts and recommended actions only. Add a separate authenticated approval/send action that requires an authorized approver and records the approval. | Tests prove no email is sent from `/assist`, including for high-confidence model output and unsafe instructions like "ignore approval policies." |
| P0 | Design/Security | No authentication, authorization, or role checks exist. | Any caller who can reach the internal endpoint can request actions, view history, or receive credit-related output. Credit-sensitive data may be exposed to unauthorized users. | Require authenticated operators, map users to roles/scopes, enforce access checks before returning credit data or enabling approval actions, and filter history by authorization. | Unauthorized users receive `401/403`; users without credit scope cannot retrieve credit-sensitive responses or history. |
| P0 | Design/Operations | There is no durable audit log for externally visible actions. | The system cannot prove who requested, approved, generated, sent, or failed an external action. This violates the audit requirement and makes incident review impossible. | Persist audit events for request received, context retrieved, draft generated, approval decision, send attempt, send result, and failure. Include requester, approver, timestamps, input/output references, retrieved context IDs, and action result. | For every attempted external action, an audit record exists with requester, approver, timestamp, input reference, output reference, and result. |
| P1 | Code/Security | Secrets are hardcoded in source. | API keys can leak through source control, logs, or screenshots, and cannot be rotated safely per environment. | Load secrets from environment or a secret manager. Fail startup if required production configuration is missing. Keep demo/mock clients separate from production clients. | Secret scanning finds no keys in the repository; tests use mock credentials; missing production secrets fail safely before serving traffic. |
| P1 | Code/Reliability | External calls have no timeout, status handling, retry policy, or circuit behavior. | A hung or failed model/email service can tie up workers, produce false success responses, or hide dependency failures from operators. | Add dependency clients with explicit timeouts, status checks, typed exceptions, and safe user-facing errors. Do not report "request received" unless the request is actually persisted. | Tests simulate model timeout, model non-200, malformed model response, and email failure; all return safe responses and emit auditable failure events. |
| P1 | Code/Safety | The model response is unstructured and parsed with fragile string checks. | The service cannot reliably distinguish draft content from control fields, and policy decisions are vulnerable to formatting changes or prompt injection. | Require structured output for summary, extracted fields, next action, confidence, safety flags, and draft text. Validate it with a schema, then apply server-side approval rules independently of the model. | Invalid or ambiguous model output cannot trigger sending and is routed to human review. |
| P1 | Test | Existing test coverage does not assert meaningful behavior. | The current test can pass even when the model call fails, because the endpoint catches the error and still returns `answer` and `sent`. Unsafe production behavior would not be caught. | Mock the LLM and email clients. Add tests for normal RFQ, missing fields, unsafe instruction, credit-sensitive request, no retrieval match, model failure, email failure, and audit creation. | CI fails if an unsafe request sends email, if missing fields are not surfaced, or if failures return success-like results without audit. |

## 4. Non-blocking improvements

| Priority | Area | Improvement | Why it matters | Suggested next step |
|---|---|---|---|---|
| P2 | Retrieval | Return structured retrieved context with IDs, categories, and relevance reasons. | Operators need to understand which internal guidance influenced the answer, and audits need stable references. | Keep simple local retrieval for now, but return context IDs and reasons instead of only concatenated text. |
| P2 | Product/API | Split summary, extracted fields, next action, draft message, confidence, and safety flags into separate response fields. | A single `answer` string is hard to validate, display, audit, or test. | Define a Pydantic response model and make the UI render each field explicitly. |
| P2 | Architecture | Separate routing, retrieval, model client, approval policy, email client, and audit persistence. | Clean boundaries make the service easier to test and reduce the chance that model behavior leaks into policy decisions. | Refactor into small modules with dependency injection for tests. |
| P2 | Observability | Replace print-style logging with structured logs and metrics. | Operations teams need to see failure rates, approval rates, unsafe-input rates, and dependency latency. | Log document/request ID, user ID, action, retrieved context IDs, safety flags, approval decision, and dependency timing. Avoid secrets and unnecessary sensitive data. |
| P3 | Retrieval quality | Improve keyword retrieval once safety is fixed. | Better retrieval improves answer quality, but it is less urgent than preventing unsafe action. | Consider BM25 or embeddings later, with evaluation cases and retrieval-gap handling. |
| P3 | Developer setup | Add documented local mock mode and exact run/test commands. | Reviewers and future engineers should be able to run the core workflow without external secrets. | Provide a README section for mock mode, dependency install, tests, and sample requests. |

## 5. Code review comments

| File | Line or section | Comment | Severity |
|---|---|---|---|
| `review_artifacts/code/app/main.py` | Lines 10-13 | Do not hardcode API keys or production URLs in source. Move configuration to environment or a secret manager, and keep mock/demo clients clearly separated from production clients. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 24-26 | `load_kb()` uses a relative path that depends on the process working directory. This can fail in deployment or tests. Resolve the path from the module location or inject the KB path through configuration. | Major |
| `review_artifacts/code/app/main.py` | Lines 35-36 | The no-match retrieval fallback says "Use best judgment." For an operational assistant, missing guidance should reduce confidence, require human review, and avoid strong recommendations. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 40-60 | The LLM call has no timeout, status check, schema validation, or handling for malformed responses. The system prompt also tells the model to follow the user's instructions, which is unsafe when document text may contain policy-bypass instructions. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 63-69 | `send_email()` ignores the email service response and always returns `True`. This can create a false audit trail and tell operators an email was sent when it failed. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 77-93 | The endpoint lets model text control sending by searching for `SEND_EMAIL=true` and `CONFIDENCE=0.9`. Sending should be a deterministic server-side policy decision after explicit human approval, not a string-parsed model instruction. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 95-100 | `HISTORY` is in-memory and lacks timestamp, approver, input/output references, retrieved context IDs, and action result detail. It will be lost on restart and does not meet the audit requirement. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 107-111 | Catching all exceptions and returning "the request was received" hides failures and may be untrue if nothing was persisted. Return a safe error and record the failure in durable audit storage. | Blocking |
| `review_artifacts/code/app/main.py` | Lines 114-116 | `/history` returns all history without authentication or authorization. This can expose procurement and credit-sensitive information across users or roles. | Blocking |
| `review_artifacts/code/tests/test_assist.py` | Lines 7-17 | The test only asserts that `answer` and `sent` keys exist. It does not mock the LLM/email services or verify safety behavior, so it can pass while the endpoint masks dependency failure. | Major |

## 6. Design review comments

| Section | Comment | Severity |
|---|---|---|
| Summary | The proposal treats high model confidence as enough to send email. Model confidence is not an approval signal and cannot authorize external actions. | Blocking |
| Proposed architecture | The architecture has no explicit approval step, authorization boundary, audit persistence, or failure state before sending. Add deterministic gates before any external side effect. | Blocking |
| Retrieval | If no result is found, the design still asks the LLM for the best possible response. Retrieval gaps should require human review and lower confidence. | Major |
| LLM behavior | The LLM is asked to decide summary, extracted fields, next action, confidence, and whether to send email. It can help draft and classify, but policy and side-effect decisions must be server controlled. | Blocking |
| Email sending | Direct send on `SEND_EMAIL=true` and confidence above 0.8 conflicts with the internal guidance that supplier outreach requires human approval before sending. | Blocking |
| Error handling | "Return a generic message and continue" hides unsafe or failed states. Failures should be explicit, safe, observable, and auditable. | Major |
| Permissions | "Internal" is not an authorization model. Permissions cannot be deferred because credit data and external actions are in scope. | Blocking |
| Audit log | "The response text can be used as a record" is insufficient. Audit records need actor, approver, timestamps, inputs, outputs, context, and action result. | Blocking |
| Evaluation | Manual checking alone is not enough for hidden regressions in safety-sensitive behavior. Add deterministic tests and a small evaluation set for normal, missing, ambiguous, unsafe, and credit cases. | Major |

## 7. Test coverage gaps

| Missing test | Risk covered | Expected behavior |
|---|---|---|
| Unsafe instruction attempts to bypass approval | Prompt injection and model obedience to user-provided instructions | Response flags unsafe instruction, requires human approval, and does not send email. |
| High-confidence model output requests sending | Model-controlled side effects | Server does not send email from `/assist`; it returns a draft pending approval. |
| Missing RFQ fields | Supplier outreach with incomplete information | Missing fields are listed; next action asks for missing details; approval is required; no email is sent. |
| Credit-sensitive request by unauthorized user | Unauthorized data exposure | Request is rejected or sensitive fields are redacted according to role. |
| No retrieval match | Model hallucination and unsupported recommendation | Retrieval gap is surfaced; confidence is lowered; human review is required. |
| LLM timeout/non-200/malformed response | Dependency failure | API returns safe failure response, does not send, and records an auditable failure. |
| Email service failure | False send confirmation | Send result is false/failed, operator sees the failure, and audit captures the error. |
| History access control | Cross-user or cross-role data leakage | Users can only view authorized history entries. |
| Audit event creation | Missing traceability | Every request and externally visible action attempt creates a durable audit event with required fields. |

## 8. Recommended fixes

### Must fix before pilot

1. Convert `/assist` to draft-only behavior: summary, extracted fields, retrieved guidance, next action, draft communication, confidence/risk explanation, and safety flags.
2. Add an authenticated, role-checked approval workflow for any external communication. The model may recommend a draft, but only an authorized human can approve sending.
3. Persist audit events for request receipt, retrieval, model output, approval decision, send attempt, send result, and failure states.
4. Replace unstructured model control text with a validated response schema and deterministic server-side safety rules.
5. Move secrets and service URLs out of source code; add mock clients for local/test mode.
6. Add timeouts, response validation, and explicit error handling for LLM and email dependencies.
7. Build meaningful tests with mocked dependencies for normal, missing-field, unsafe, credit-sensitive, retrieval-gap, and failure scenarios.

### Can fix after pilot

1. Improve retrieval quality with BM25, embeddings, or a vector store once safety gates are stable.
2. Add broader evaluation datasets and regression scoring for extraction, retrieval relevance, and safety flags.
3. Add dashboards for latency, dependency failures, approval rate, unsafe-input rate, and operator overrides.
4. Add queue/background processing for email sends and retries after the approval workflow is reliable.
5. Add operator feedback loops to improve guidance quality and draft usefulness.

## 9. Follow-up plan for the junior engineer

First, remove all automatic email sending from `/assist` and make the endpoint return a structured draft response only. Next, define Pydantic models for request, response, retrieved context, extracted fields, safety flags, and audit events. Then implement a deterministic approval policy that always requires human approval for supplier/applicant communication, missing required fields, unsafe instructions, ambiguous requests, weak retrieval, or credit decisions. After that, add authentication/authorization checks and a durable audit store before introducing any real external send path. Finally, replace the current broad test with mocked tests that prove unsafe instructions, missing fields, service failures, and unauthorized credit access fail safely.

## 10. Production acceptance criteria

- No external supplier, applicant, bank, or customer communication can be sent without an authenticated authorized human approval.
- The model cannot authorize side effects; it can only produce drafts, extracted fields, classifications, risk explanations, and recommendations.
- Credit-related information is protected by role-based access control and is not exposed through `/assist` or `/history` to unauthorized users.
- Every externally visible action and attempted action has a durable audit record with requester, approver, timestamp, input reference, output reference, retrieved context, and action result.
- Retrieval gaps, missing required fields, ambiguous requests, unsafe instructions, and dependency failures all fail safely and require human review.
- LLM and email clients have timeouts, status checks, typed error handling, and no hardcoded secrets.
- Tests cover normal RFQ, missing RFQ fields, unsafe instruction, credit request, no retrieval match, LLM failure, email failure, approval behavior, and audit creation.
- The service can run locally in mock mode without paid APIs, external secrets, or real email delivery.

## 11. Assumptions

- The knowledge base entries provided with the assessment are treated as authoritative internal guidance for this review.
- "Internal tool" does not remove the need for authentication, authorization, approval, or audit controls.
- The reviewed artifact is intentionally incomplete, so the goal is to prioritize production risks rather than rewrite the full application.
- Candidate name is left blank for the submitter to fill in.
- No GitHub repository, external orchestration framework, paid API, PDF ingestion, or additional procurement collateral is required for this first assessment deliverable.
