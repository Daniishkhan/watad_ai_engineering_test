# Lead Review Gauntlet — Candidate Package

## Your role

You are the technical lead reviewing work from a less senior engineer.

The work is intended for an internal AI assistant used in procurement, supplier, or credit operations. Your task is to review the provided design and code as if it may be shipped into a real operational workflow.

You are not expected to rewrite the solution. Your job is to review, prioritize, and guide the engineer toward a production-safe version.

## Timebox

Total time: 2 hours

Recommended split:

- 60 minutes: code review
- 40 minutes: design review
- 20 minutes: prioritization and final recommendation

## What you will review

This package includes:

- Product requirement
- Junior engineer design proposal
- Python/FastAPI code sample
- Weak test file
- Small knowledge base sample
- Submission template

## Your required output

Submit one document using `SUBMISSION_TEMPLATE.md`.

Your review must include:

1. Review summary
2. Blocking issues
3. Non-blocking improvements
4. Code review comments
5. Design review comments
6. Test coverage gaps
7. Recommended fixes
8. Final decision: approve, revise, or reject
9. Short follow-up plan for the junior engineer
10. Production acceptance criteria

## Rules

- Do not spend the assessment rewriting the full application.
- Do not assume missing infrastructure exists unless you state it as an assumption.
- Prioritize production risk over style preferences.
- Be direct but constructive.
- Mention impact and recommended fix for every important issue.
- Separate blockers from non-blocking improvements.
- Keep your answer concise enough for a real engineering review.

## What strong review looks like

A strong review identifies the highest-risk issues first, explains why they matter, and gives practical next steps a less senior engineer could execute.

The goal is not to find the maximum number of comments.

The goal is to find the issues that matter most before this work reaches production.

## Confidentiality

This exercise uses synthetic data and a fictional internal workflow. Do not include confidential information from your current or past employers in your response.
