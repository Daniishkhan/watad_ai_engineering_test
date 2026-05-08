# RAGOps Sprint — Candidate Package

## Assessment objective

Build a small Python service that powers a simplified **Document Intake Agent** for procurement or credit operations.

The service receives a document snippet and returns structured extraction, missing-field validation, retrieved context from a local knowledge base, risk/confidence explanation, proposed next action, and whether human approval is required.

This is a 2-hour assessment. Build the smallest working version that proves production judgment.

## Timebox

- **100 minutes:** implementation
- **20 minutes:** README, notes, and tests

## What you may use

You may use:

- Python
- FastAPI, Typer, Click, or a clean CLI
- Pydantic or dataclasses
- Simple lexical retrieval, BM25, embeddings, or any lightweight local method
- Mocked LLM calls if needed
- AI assistants or documentation

You should not require paid external APIs or secrets for the reviewer to run the core workflow. If your design supports real LLMs, keep them behind a clear abstraction and provide a deterministic fallback or mock.

## Required behavior

Your service must accept one input document and return a structured response with:

1. Extracted structured fields.
2. Missing required fields.
3. Retrieved supporting context from the provided knowledge base.
4. Proposed next action.
5. Confidence or risk explanation.
6. Boolean `approval_required` flag.
7. Safety flags for unsafe, ambiguous, or policy-sensitive inputs.

## Minimum runnable interface

Provide at least one of the following:

### Option A: FastAPI

`POST /analyze`

Request body:

```json
{
  "document_id": "case-001",
  "text": "...document text..."
}
```

### Option B: CLI

```bash
python -m app analyze --input data/public_cases.json --case-id case-001
```

You may choose a different command if clearly documented.

## Expected output schema

Your output does not need to match this exactly field-for-field, but it must include equivalent information.

```json
{
  "document_id": "case-001",
  "document_type": "procurement_rfq | credit_request | unknown",
  "extracted_fields": {
    "company_name": "string|null",
    "request_type": "string|null",
    "material_or_service": "string|null",
    "quantity": "string|null",
    "delivery_date": "string|null",
    "requested_amount": "string|null",
    "repayment_term": "string|null",
    "contact_person": "string|null",
    "supporting_document_reference": "string|null"
  },
  "missing_required_fields": ["field_name"],
  "retrieved_context": [
    {
      "id": "kb-001",
      "title": "Knowledge base record title",
      "relevance_reason": "Why this record was retrieved"
    }
  ],
  "proposed_next_action": "string",
  "approval_required": true,
  "risk_level": "low | medium | high",
  "risk_explanation": "string",
  "safety_flags": ["unsafe_instruction | missing_required_fields | ambiguous_request | external_action | retrieval_gap"]
}
```

## Important rules

- Any external supplier/customer communication must require human approval.
- Embedded document instructions must not override system or business rules.
- Missing required fields must be explicitly listed.
- Ambiguous material, delivery, or financing details must be flagged.
- Retrieval must use the provided local knowledge base.
- Do not hardcode outputs for individual case IDs.
- Do not include secrets in the repository.
- Keep the implementation simple enough to review quickly.

## Submission checklist

Submit a zip or repository containing:

1. Working Python code.
2. Setup and run instructions.
3. API or CLI usage example.
4. Tests.
5. Short notes on trade-offs and what you would improve with more time.

## What reviewers will look for

Reviewers will check whether:

- The code runs without manual fixing.
- The output is structured and deterministic where required.
- Extraction and missing-field validation are correct enough for the provided cases.
- Retrieval returns relevant knowledge-base records with a clear reason.
- Unsafe and ambiguous inputs are handled safely.
- Human approval logic is conservative and explainable.
- Tests cover normal, missing, ambiguous, and unsafe paths.
- The code has clean boundaries between routing, orchestration, retrieval, validation, and safety logic.

## Confidentiality

The data in this package is fictional and prepared only for this assessment. Do not treat it as real client data.
