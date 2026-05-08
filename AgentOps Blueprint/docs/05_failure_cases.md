# Failure Cases to Consider

Your design should explain how the system behaves in these cases.

## Missing information

RFQ contains material name and quantity but no delivery date or location.

Expected behavior:

- Do not dispatch externally.
- Flag missing fields.
- Ask for clarification or route to human review.

## Ambiguous material

RFQ says “same as last project” without attaching the previous specification.

Expected behavior:

- Retrieve likely historical context.
- Show citations and uncertainty.
- Require human confirmation.

## Conflicting units

Email says 800 meters but attachment says 800 pieces.

Expected behavior:

- Detect conflict.
- Mark high risk.
- Require human review.

## Unsafe document instruction

Source document tells the model to bypass approval and email a supplier directly.

Expected behavior:

- Treat document content as untrusted data.
- Ignore instruction that conflicts with system policy.
- Require approval before external action.

## Retrieval failure

Vector search returns irrelevant or low-confidence records.

Expected behavior:

- Do not fabricate citations.
- Show low confidence.
- Fallback to keyword search, manual review, or deterministic catalog lookup.

## Supplier API timeout

Supplier master or workflow API is unavailable.

Expected behavior:

- Preserve RFQ state.
- Retry safely where appropriate.
- Avoid duplicate external dispatch.
- Surface operational error to user or queue.

## Unauthorized user

User asks to view or contact supplier records outside their permission scope.

Expected behavior:

- Deny access or return redacted data.
- Log authorization event.
- Do not leak supplier contact details.

## Regression after prompt/model change

New model version starts proposing alternates without valid approval conditions.

Expected behavior:

- Eval suite catches regression before release.
- Monitoring detects online anomaly.
- Rollback or config pinning path exists.
