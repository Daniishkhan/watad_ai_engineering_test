"""Command-line interface for the document intake analyzer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_document, load_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Analyze procurement or credit intake snippets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="analyze one document")
    analyze_parser.add_argument("--input", help="JSON file containing document cases")
    analyze_parser.add_argument("--case-id", help="document_id to select from --input")
    analyze_parser.add_argument("--document-id", help="document_id to use with --text")
    analyze_parser.add_argument("--text", help="raw document text to analyze")
    analyze_parser.add_argument(
        "--kb",
        default="data/knowledge_base.json",
        help="path to local knowledge base JSON",
    )
    analyze_parser.add_argument(
        "--required-fields",
        default="data/required_fields.json",
        help="path to required field rules JSON",
    )

    args = parser.parse_args(argv)
    if args.command == "analyze":
        return run_analyze(args)
    return 2


def run_analyze(args: argparse.Namespace) -> int:
    try:
        knowledge_base = load_json(Path(args.kb))
        required_fields = load_json(Path(args.required_fields))
        documents = resolve_documents(args)
        results = [
            analyze_document(
                document["document_id"],
                document["text"],
                knowledge_base,
                required_fields,
            )
            for document in documents
        ]
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = results[0] if len(results) == 1 else results
    print(json.dumps(output, indent=2, sort_keys=False))
    return 0


def resolve_documents(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.text:
        return [
            {
                "document_id": args.document_id or args.case_id or "ad-hoc",
                "text": args.text,
            }
        ]

    if not args.input:
        raise ValueError("provide either --text or --input")

    cases = load_json(Path(args.input))
    if not isinstance(cases, list):
        raise ValueError("--input must point to a JSON array of documents")

    if args.case_id:
        for case in cases:
            if case.get("document_id") == args.case_id:
                validate_case(case)
                return [{"document_id": case["document_id"], "text": case["text"]}]
        raise ValueError(f"case_id not found: {args.case_id}")

    for case in cases:
        validate_case(case)
    return [{"document_id": case["document_id"], "text": case["text"]} for case in cases]


def validate_case(case: dict[str, str]) -> None:
    if "document_id" not in case or "text" not in case:
        raise ValueError("each input document must include document_id and text")


if __name__ == "__main__":
    raise SystemExit(main())
