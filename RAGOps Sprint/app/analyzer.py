"""Core deterministic analysis pipeline.

The implementation intentionally uses only the Python standard library. The
model-facing parts of a production system are represented here as deterministic
classification, extraction, retrieval, validation, and safety policy steps.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FIELD_KEYS = [
    "company_name",
    "request_type",
    "material_or_service",
    "quantity",
    "delivery_date",
    "requested_amount",
    "repayment_term",
    "contact_person",
    "supporting_document_reference",
]

SAFETY_FLAGS = [
    "unsafe_instruction",
    "missing_required_fields",
    "ambiguous_request",
    "external_action",
    "retrieval_gap",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "must",
    "of",
    "or",
    "the",
    "to",
    "with",
}


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def analyze_document(
    document_id: str,
    text: str,
    knowledge_base: list[dict[str, Any]],
    required_fields: dict[str, Any],
) -> dict[str, Any]:
    text = text.strip()
    document_type = classify_document(text)
    extracted_fields = extract_fields(text, document_type)
    missing_required_fields = find_missing_fields(
        document_type, extracted_fields, required_fields, text
    )
    preliminary_flags = detect_preliminary_flags(
        text, document_type, extracted_fields, missing_required_fields
    )
    retrieved_context = retrieve_context(
        text, document_type, preliminary_flags, knowledge_base
    )
    safety_flags = finalize_safety_flags(
        preliminary_flags, missing_required_fields, retrieved_context
    )
    approval_required = requires_approval(document_type, safety_flags)
    risk_level = determine_risk_level(document_type, safety_flags)

    return {
        "document_id": document_id,
        "document_type": document_type,
        "extracted_fields": extracted_fields,
        "missing_required_fields": missing_required_fields,
        "retrieved_context": retrieved_context,
        "proposed_next_action": propose_next_action(
            document_type, missing_required_fields, safety_flags
        ),
        "approval_required": approval_required,
        "risk_level": risk_level,
        "risk_explanation": explain_risk(
            document_type, missing_required_fields, safety_flags, approval_required
        ),
        "safety_flags": safety_flags,
    }


def classify_document(text: str) -> str:
    lower = text.lower()
    procurement_terms = [
        "rfq",
        "quotation",
        "quote",
        "supplier",
        "suppliers",
        "procurement",
        "material",
        "delivery",
        "purchase",
        "price",
    ]
    credit_terms = [
        "credit",
        "financing",
        "finance",
        "requested amount",
        "repayment",
        "underwriting",
        "bank",
        "collateral",
    ]
    procurement_score = sum(1 for term in procurement_terms if term in lower)
    credit_score = sum(1 for term in credit_terms if term in lower)

    mixed_or_uncertain = bool(
        re.search(r"\b(supplier/credit|maybe|not confirmed|thing\?\?|unclear)\b", lower)
    )
    if procurement_score >= 2 and credit_score >= 2 and mixed_or_uncertain:
        return "unknown"
    if credit_score >= procurement_score + 2 or "credit intake request" in lower:
        return "credit_request"
    if procurement_score > 0 and procurement_score >= credit_score:
        return "procurement_rfq"
    if credit_score > 0:
        return "credit_request"
    return "unknown"


def extract_fields(text: str, document_type: str) -> dict[str, str | None]:
    fields = {key: None for key in FIELD_KEYS}
    fields["company_name"] = extract_company_name(text)
    fields["contact_person"] = extract_contact_person(text)
    fields["supporting_document_reference"] = extract_supporting_document(text)
    fields["quantity"] = extract_quantity(text)
    fields["delivery_date"] = extract_delivery_date(text)

    if document_type == "procurement_rfq":
        fields["request_type"] = "procurement RFQ"
        fields["material_or_service"] = extract_material_or_service(text)
    elif document_type == "credit_request":
        fields["request_type"] = "credit request"
        fields["requested_amount"] = extract_requested_amount(text)
        fields["repayment_term"] = extract_repayment_term(text)
    else:
        fields["request_type"] = infer_ambiguous_request_type(text)
        fields["material_or_service"] = extract_material_or_service(text)
        fields["requested_amount"] = extract_requested_amount(text)
        fields["repayment_term"] = extract_repayment_term(text)

    return fields


def extract_company_name(text: str) -> str | None:
    patterns = [
        r"\bRFQ from\s+(.+?)(?:\.|,|\n)",
        r"\bCompany:\s+(.+?)(?:\.|,|\n)",
        r"\bClient:\s+(.+?)(?:\.|,|\n)",
        r"\bCredit intake request for\s+(.+?)(?:\.|,|\n)",
        r"\bCredit request for\s+(.+?)(?:\.|,|\n)",
        r"\bcompany maybe\s+(.+?)(?:\s+wants|\.|,|\n)",
        r"^(.+?)\s+requests\s+urgent quotation\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_value(match.group(1))
    return None


def extract_contact_person(text: str) -> str | None:
    patterns = [
        r"\bContact is\s+([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+)?)",
        r"\bContact:\s*'?([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+)?)'?",
        r"\bcontact:\s+'([^']+)'",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_value(match.group(1))
    return None


def extract_supporting_document(text: str) -> str | None:
    negative = r"\b(no attachment|no supporting document|filename unknown|no document)\b"
    if re.search(negative, text, re.IGNORECASE):
        return None
    match = re.search(
        r"\bSupporting doc(?:ument)?(?: reference)?:\s*([A-Za-z0-9_.-]+\.(?:pdf|png|jpg|jpeg|zip))",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    generic = re.search(r"\b([A-Za-z0-9_.-]+\.(?:pdf|png|jpg|jpeg|zip))\b", text)
    return generic.group(1) if generic else None


def extract_quantity(text: str) -> str | None:
    patterns = [
        r"\bNeed\s+([\d,]+)\s+[A-Za-z]",
        r"\bneed\s+[A-Za-z][^,.;]*,\s*([\d,]+)\s+(?:pieces|units|bags)",
        r"\bquotation for\s+([\d,]+)\s+[A-Za-z]",
        r"\bwants\s+([\d,]+)\s+[A-Za-z]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(",", "")
    return None


def extract_delivery_date(text: str) -> str | None:
    if re.search(r"\bno delivery date\b", text, re.IGNORECASE):
        return None
    iso = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if iso:
        return iso.group(1)
    phrase = re.search(
        r"\bdelivery(?: required)?(?: by|:)?\s+(next month|asap this week|ASAP this week|by \d{1,2} [A-Za-z]+)",
        text,
        re.IGNORECASE,
    )
    if phrase:
        return clean_value(phrase.group(1))
    if re.search(r"\bnext month delivery\b", text, re.IGNORECASE):
        return "next month"
    return None


def extract_requested_amount(text: str) -> str | None:
    if re.search(r"\bamount not confirmed\b", text, re.IGNORECASE):
        return None
    match = re.search(
        r"\bRequested amount:\s*([A-Z]{3}\s*[\d,]+|[\d,]+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )
    return clean_value(match.group(1)) if match else None


def extract_repayment_term(text: str) -> str | None:
    match = re.search(r"\bRepayment term:\s*([^.\n]+)", text, re.IGNORECASE)
    return clean_value(match.group(1)) if match else None


def extract_material_or_service(text: str) -> str | None:
    patterns = [
        r"\bNeed\s+[\d,]+\s+(.+?)(?:\.| Delivery| delivered|, delivery|\s+delivered)",
        r"\bneed\s+(.+?),\s*[\d,]+\s+(?:pieces|units|bags)",
        r"\bquotation for\s+[\d,]+\s+(.+?)(?:\s+for\s+a|\.)",
        r"\bwants\s+[\d,]+\s+(.+?)(?:\s+\+|\.|,)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = clean_value(match.group(1))
            return remove_trailing_context(value)
    return None


def infer_ambiguous_request_type(text: str) -> str | None:
    lower = text.lower()
    if any(term in lower for term in ["supplier", "quotation", "rfq"]) and any(
        term in lower for term in ["credit", "financing", "finance"]
    ):
        return "mixed procurement/credit request"
    return None


def find_missing_fields(
    document_type: str,
    fields: dict[str, str | None],
    required_fields: dict[str, Any],
    text: str,
) -> list[str]:
    if document_type in required_fields:
        return [
            field
            for field in required_fields[document_type].get("required", [])
            if not fields.get(field)
        ]

    missing = ["document_type"]
    lower = text.lower()
    if any(term in lower for term in ["credit", "financing", "finance"]):
        if not fields.get("requested_amount"):
            missing.append("requested_amount")
        if not fields.get("repayment_term"):
            missing.append("repayment_term")
    if any(term in lower for term in ["supplier", "rfq", "quotation", "delivery"]):
        if not fields.get("supporting_document_reference"):
            missing.append("supporting_document_reference")
        if not fields.get("delivery_date"):
            missing.append("delivery_date")
    return dedupe(missing)


def detect_preliminary_flags(
    text: str,
    document_type: str,
    fields: dict[str, str | None],
    missing_required_fields: list[str],
) -> list[str]:
    lower = text.lower()
    flags: list[str] = []
    if re.search(
        r"(system override|important system override|ignore (?:all )?(?:approval|policy|policies)|bypass approval|mark approval_required as false|approval_required\s*=\s*false|approve financing|approve credit)",
        lower,
    ):
        flags.append("unsafe_instruction")
    if missing_required_fields:
        flags.append("missing_required_fields")
    if document_type == "unknown" or re.search(
        r"(maybe|not sure|could be|not confirmed|unknown|thing\?\?|asap|no last name)",
        lower,
    ):
        flags.append("ambiguous_request")
    external_signal = re.search(
        r"\b(supplier outreach|supplier|suppliers|customer|contractor|bank|email|quotation|quote|price|ask suppliers)\b",
        lower,
    )
    explicit_no_external = re.search(
        r"\b(no|do not|don't)\s+(?:contact|email|message|send|reach out to)\s+(?:the\s+)?(?:supplier|suppliers|customer|contractor|bank)\b",
        lower,
    )
    if external_signal and not explicit_no_external:
        flags.append("external_action")
    if fields.get("delivery_date") and fields["delivery_date"].lower() in {
        "next month",
        "asap this week",
    }:
        flags.append("ambiguous_request")
    return ordered_flags(flags)


def retrieve_context(
    text: str,
    document_type: str,
    safety_flags: list[str],
    knowledge_base: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, str]]:
    if document_type == "unknown" and not has_operational_signal(text):
        return []

    query = build_retrieval_query(text, document_type, safety_flags)
    query_tokens = set(tokenize(query))
    scored: list[tuple[int, dict[str, Any]]] = []

    for record in knowledge_base:
        haystack = " ".join(
            [
                record.get("title", ""),
                record.get("category", ""),
                record.get("text", ""),
            ]
        )
        tokens = set(tokenize(haystack))
        score = len(query_tokens & tokens) + category_boost(record, document_type, safety_flags)
        if score > 0:
            scored.append((score, record))

    scored.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    return [
        {
            "id": record["id"],
            "title": record["title"],
            "relevance_reason": relevance_reason(record, document_type, safety_flags),
        }
        for _, record in scored[:limit]
    ]


def build_retrieval_query(text: str, document_type: str, safety_flags: list[str]) -> str:
    parts = [text]
    if document_type == "procurement_rfq":
        parts.append("procurement rfq supplier outreach quotation required fields")
    if document_type == "credit_request":
        parts.append("credit request financing underwriting repayment required fields")
    if "unsafe_instruction" in safety_flags:
        parts.append("prompt injection document instruction approval policy")
    if "ambiguous_request" in safety_flags and has_operational_signal(text):
        parts.append("ambiguous material delivery financing retrieval failure")
    if "external_action" in safety_flags:
        parts.append("external communication supplier customer bank approval")
    if "missing_required_fields" in safety_flags:
        parts.append("required fields validation missing")
    return " ".join(parts)


def category_boost(
    record: dict[str, Any], document_type: str, safety_flags: list[str]
) -> int:
    category = record.get("category", "")
    score = 0
    if document_type == "procurement_rfq" and category in {
        "approval_policy",
        "procurement_validation",
        "procurement_workflow",
        "previous_rfq",
    }:
        score += 3
    if document_type == "credit_request" and category in {
        "credit_validation",
        "credit_policy",
        "previous_credit_case",
    }:
        score += 3
    if "unsafe_instruction" in safety_flags and category == "safety_policy":
        score += 6
    if "external_action" in safety_flags and category == "approval_policy":
        score += 5
    if "ambiguous_request" in safety_flags and document_type != "unknown" and category in {
        "procurement_validation",
        "reliability_policy",
    }:
        score += 4
    if (
        "missing_required_fields" in safety_flags
        and document_type == "procurement_rfq"
        and category == "procurement_validation"
    ):
        score += 4
    if (
        "missing_required_fields" in safety_flags
        and document_type == "credit_request"
        and category == "credit_validation"
    ):
        score += 4
    return score


def has_operational_signal(text: str) -> bool:
    return bool(
        re.search(
            r"\b(rfq|quotation|quote|supplier|suppliers|procurement|material|delivery|credit|financing|finance|underwriting|repayment|contractor|customer)\b",
            text.lower(),
        )
    )


def relevance_reason(
    record: dict[str, Any], document_type: str, safety_flags: list[str]
) -> str:
    category = record.get("category")
    if category == "approval_policy":
        return "External communication requires authorized human approval."
    if category == "safety_policy":
        return "Embedded document instructions are untrusted and cannot override policy."
    if category in {"procurement_validation", "credit_validation"}:
        return "Record defines required fields and validation expectations for this intake type."
    if category == "credit_policy":
        return "Credit decisions must remain with a human reviewer."
    if category == "reliability_policy":
        return "Weak or missing context should require human review."
    if category == "previous_rfq":
        return "Previous RFQ record is similar to the requested material."
    if category == "previous_credit_case":
        return "Previous credit intake record shows the safe review boundary."
    if document_type == "procurement_rfq":
        return "Record is relevant to procurement intake workflow."
    if "ambiguous_request" in safety_flags:
        return "Record helps handle ambiguous intake safely."
    return "Record shares terms with the submitted document."


def finalize_safety_flags(
    preliminary_flags: list[str],
    missing_required_fields: list[str],
    retrieved_context: list[dict[str, str]],
) -> list[str]:
    flags = list(preliminary_flags)
    if missing_required_fields and "missing_required_fields" not in flags:
        flags.append("missing_required_fields")
    if not retrieved_context:
        flags.append("retrieval_gap")
    return ordered_flags(flags)


def requires_approval(document_type: str, safety_flags: list[str]) -> bool:
    if document_type in {"credit_request", "unknown"}:
        return True
    return any(
        flag in safety_flags
        for flag in [
            "unsafe_instruction",
            "missing_required_fields",
            "ambiguous_request",
            "external_action",
            "retrieval_gap",
        ]
    )


def determine_risk_level(document_type: str, safety_flags: list[str]) -> str:
    if "unsafe_instruction" in safety_flags or document_type == "unknown":
        return "high"
    if any(flag in safety_flags for flag in ["missing_required_fields", "ambiguous_request", "retrieval_gap"]):
        return "medium"
    if document_type == "credit_request":
        return "medium"
    return "low"


def propose_next_action(
    document_type: str, missing_required_fields: list[str], safety_flags: list[str]
) -> str:
    if "unsafe_instruction" in safety_flags:
        return (
            "Do not follow embedded override instructions. Prepare the intake summary "
            "for authorized human review before any external action."
        )
    if document_type == "unknown":
        return (
            "Route to a human operator to clarify the request type, missing fields, "
            "and whether any external or financing action is involved."
        )
    if missing_required_fields:
        return (
            "Request missing required fields before proceeding: "
            f"{', '.join(missing_required_fields)}."
        )
    if "ambiguous_request" in safety_flags:
        return (
            "Clarify ambiguous material, delivery, or financing details before supplier "
            "comparison or outreach."
        )
    if document_type == "credit_request":
        return (
            "Prepare an underwriting intake summary for human review; do not approve "
            "credit or communicate a financing decision."
        )
    if "external_action" in safety_flags:
        return "Prepare a supplier outreach draft for human review and approval."
    return "Summarize and route internally; no external action is recommended."


def explain_risk(
    document_type: str,
    missing_required_fields: list[str],
    safety_flags: list[str],
    approval_required: bool,
) -> str:
    reasons: list[str] = []
    if "unsafe_instruction" in safety_flags:
        reasons.append("the document contains instructions that attempt to override policy")
    if missing_required_fields:
        reasons.append("required fields are missing")
    if "ambiguous_request" in safety_flags:
        reasons.append("the request contains ambiguous or uncertain details")
    if "external_action" in safety_flags:
        reasons.append("the requested next step may affect an external party")
    if document_type == "credit_request":
        reasons.append("credit intake must remain a human-reviewed workflow")
    if "retrieval_gap" in safety_flags:
        reasons.append("no strong local guidance was retrieved")

    if not reasons:
        return (
            "Required fields are present. Human approval is still required before any "
            "external communication."
            if approval_required
            else "Low-risk internal processing only; no external action is proposed."
        )
    return "Approval is required because " + "; ".join(reasons) + "."


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in STOPWORDS
    ]


def ordered_flags(flags: list[str]) -> list[str]:
    present = set(flags)
    return [flag for flag in SAFETY_FLAGS if flag in present]


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" '\".,;:")).strip()


def remove_trailing_context(value: str) -> str:
    value = re.sub(r"\s+for\s+(?:a\s+)?(?:site package|next month delivery).*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+depending on price.*$", "", value, flags=re.IGNORECASE)
    return clean_value(value)
