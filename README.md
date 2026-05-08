# Watad AI Engineering Test

This repository contains three assessment submissions:

- `Lead Review Gauntlet/` - technical lead review of a proposed internal operations assistant.
- `RAGOps Sprint/` - runnable deterministic document intake agent for procurement and credit operations.
- `AgentOps Blueprint/` - architecture package for a production Procurement RFQ Agent.

## Recommended review path

1. Read the completed lead review submission:

   ```text
   Lead Review Gauntlet/Danish_Khan_Lead_Review_Gauntlet_Submission.md
   ```

   The original template for this assessment is also included at:

   ```text
   Lead Review Gauntlet/SUBMISSION_TEMPLATE.md
   ```

2. Run the RAGOps Sprint implementation:

   ```bash
   cd "RAGOps Sprint"
   python3 -m app analyze --input data/public_cases.json --case-id case-001-normal-rfq
   python3 -m unittest discover -s tests
   ```

3. Review the RAGOps implementation notes:

   ```text
   RAGOps Sprint/README.md
   ```

4. Read the AgentOps Blueprint submission:

   ```text
   AgentOps Blueprint/Danish_Khan_AgentOps_Blueprint_Submission.md
   ```

   The original add-on assessment materials are under:

   ```text
   AgentOps Blueprint/docs/
   ```

## RAGOps quick commands

Analyze all public cases:

```bash
cd "RAGOps Sprint"
python3 -m app analyze --input data/public_cases.json
```

Analyze custom text:

```bash
cd "RAGOps Sprint"
python3 -m app analyze \
  --document-id custom-001 \
  --text "RFQ from GulfBuild Contracting LLC. Need 500 galvanized steel pipes delivered by 2026-06-15. Contact: Sara Malik. Supporting document: RFQ-GB-2026-114.pdf. Prepare supplier outreach draft."
```

Run tests:

```bash
cd "RAGOps Sprint"
python3 -m unittest discover -s tests
```

## Notes

- The RAGOps Sprint implementation uses only the Python standard library.
- No paid APIs, secrets, external services, LangGraph, FastAPI, or LLM calls are required to run the core workflow.
- Original RAGOps prompt/supporting materials are under `RAGOps Sprint/docs/`.
- The Lead Review folder keeps the original reviewed artifacts in place because the completed review references them directly.
- The AgentOps Blueprint folder is design-only because that add-on assessment asks for an architecture package, not code.
