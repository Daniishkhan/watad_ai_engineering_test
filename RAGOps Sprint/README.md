# RAGOps Sprint - Document Intake Agent

This is a small deterministic Python intake agent for procurement RFQ and credit request snippets. It extracts key fields, validates missing required information, retrieves supporting local guidance, applies conservative approval/safety rules, and returns structured JSON.

The implementation uses only the Python standard library. It does not require paid APIs, secrets, LangGraph, FastAPI, or an LLM to run the core workflow.

## How to run

From this folder:

```bash
python3 -m app analyze --input data/public_cases.json --case-id case-001-normal-rfq
```

Analyze all public cases:

```bash
python3 -m app analyze --input data/public_cases.json
```

Analyze ad hoc text:

```bash
python3 -m app analyze \
  --document-id custom-001 \
  --text "RFQ from GulfBuild Contracting LLC. Need 500 galvanized steel pipes delivered by 2026-06-15. Contact: Sara Malik. Supporting document: RFQ-GB-2026-114.pdf. Prepare supplier outreach draft."
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

## Output

The CLI prints JSON with:

- `document_id`
- `document_type`
- `extracted_fields`
- `missing_required_fields`
- `retrieved_context`
- `proposed_next_action`
- `approval_required`
- `risk_level`
- `risk_explanation`
- `safety_flags`

## Design choices

- **Service structure:** `app/__main__.py` handles the CLI, while `app/analyzer.py` contains the deterministic analysis pipeline.
- **Retrieval method:** simple lexical scoring over the provided local knowledge base, with small policy-aware boosts for procurement, credit, unsafe instruction, ambiguity, and external action signals.
- **Validation method:** document type is inferred from text signals, then required fields are checked from `data/required_fields.json`.
- **Safety and approval logic:** any external communication, missing fields, unsafe override instruction, ambiguity, retrieval gap, unknown request, or credit workflow requires human approval.
- **LLM behavior:** no LLM is needed for this runnable version. A production LLM adapter could draft richer summaries later, but approval and safety policy should remain deterministic server-side logic.

## Tests included

The unittest suite covers:

- normal procurement RFQ extraction and approval requirement
- missing RFQ delivery date and supporting document
- ambiguous material/delivery details
- unsafe embedded instruction that tries to bypass approval
- credit intake extraction and human-review boundary
- messy mixed procurement/credit input
- hidden-style unrelated input with retrieval gap

## Known limitations

- Field extraction is heuristic and optimized for short operational snippets, not arbitrary documents.
- The CLI accepts normalized text; PDF/OCR/email ingestion is intentionally out of scope for this two-hour version.
- Retrieval is lexical and local only; it does not use embeddings or a vector database.
- There is no persistent audit store or RBAC because this assessment asks for a runnable core workflow, not production infrastructure.

## Production improvements

- Add a text ingestion layer for email, PDF/OCR, and attachment metadata.
- Add an evaluation dataset with regression checks for extraction, retrieval relevance, and safety flags.
- Add structured logging, tracing, durable audit events, and operator feedback.
- Add RBAC and tenant-aware document access before exposing credit-sensitive workflows.
- Consider a real LLM/tool-call adapter only after deterministic approval and safety gates are stable.

## Docs

The original assessment notes and schema example are kept under `docs/` for reference. The runnable app uses `data/knowledge_base.json`, `data/required_fields.json`, and optional input files such as `data/public_cases.json`.
