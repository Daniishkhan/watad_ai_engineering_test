# Product Requirement

## Feature name

Internal Operations Assistant

## Background

Operations teams receive supplier requests, procurement documents, and credit-related emails. They need a lightweight assistant that can summarize incoming requests, search internal guidance, and prepare the next action for a human operator.

## Requested behavior

The assistant should:

1. Accept a free-text request from an internal operator.
2. Retrieve relevant internal guidance from a small knowledge base.
3. Produce a short summary.
4. Extract key fields when possible.
5. Suggest the next operational action.
6. Draft supplier or applicant communication when relevant.
7. Send the communication automatically when confidence is high.
8. Keep enough history to help operators understand what happened.

## Business goal

Reduce manual triage time for routine procurement and credit operations.

## Initial constraints

- This is an internal tool.
- The first version will be used by a small operations team.
- Supplier outreach must be accurate and traceable.
- Credit-related outputs must not expose sensitive data to unauthorized users.
- External messages should not be sent without the correct approval.
- Every externally visible action should be auditable.
- The system should fail safely if the model, retrieval, or external service is unavailable.

## Expected reviewer judgment

Review whether the proposed design and code are safe enough to continue toward production.

You may recommend approve, revise, or reject.
