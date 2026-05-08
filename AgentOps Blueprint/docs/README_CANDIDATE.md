# TrueSkill Assessment Package
## AgentOps Blueprint

This package supports the AgentOps Blueprint assessment.

You have 2 hours total:

- 90 minutes for architecture and workflow design
- 30 minutes for assumptions, risks, trade-offs, and final cleanup

Your task is to design a production-ready Procurement RFQ Agent for a contractor/supplier workflow.

Do not build code. Produce a concise architecture package that could be reviewed by engineering, product, security, and operations.

## What to submit

Submit one PDF, Markdown file, or shared document containing:

1. System architecture diagram or structured architecture description
2. Workflow/state-machine design
3. Tool and service boundaries
4. Data model sketch
5. API surface sketch
6. Retrieval strategy
7. Evaluation and observability plan
8. Security, approval, and audit controls
9. Cost, latency, and reliability trade-offs
10. Explicit assumptions and out-of-scope items

## Allowed tools

You may use diagrams, notes, AI tools, documentation, or your own templates.

We care less about the tool used and more about the quality of your technical judgment.

## Important constraint

No external supplier communication may happen without explicit human approval.

Design for production behavior, not demo behavior.

## Files in this package

- `01_case_context.md` — business scenario and user workflow
- `02_source_systems.md` — available systems, records, and integration points
- `03_sample_records.md` — sample RFQs, supplier records, previous RFQs, and approved alternates
- `04_operational_constraints.md` — reliability, security, latency, and workflow constraints
- `05_failure_cases.md` — scenarios your design should handle
- `06_submission_template.md` — recommended structure for your answer
- `data/sample_records.json` — machine-readable version of the sample records

## Evaluation summary

Your submission will be evaluated on production suitability, agent/tool boundaries, retrieval and citation quality, reliability, human approval controls, observability, security, auditability, and practical trade-offs.

We are not looking for a beautiful diagram.

We are looking for evidence that the system would survive real enterprise workflow constraints.

## Agency disclaimer

This assessment was prepared by HireTrust for skills-based evaluation purposes only.
It is not an employment offer, contract, or guarantee of selection. Candidate submissions will be reviewed confidentially and used solely to assess role-relevant technical capability, judgment, and fit for the hiring process.
