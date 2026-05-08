from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
from typing import Dict, Any

app = FastAPI(title="Internal Operations Assistant")

# TODO: Move later if pilot works
OPENAI_API_KEY = "sk-demo-hardcoded-key-do-not-use"
EMAIL_API_KEY = "email-demo-key"
LLM_URL = "https://api.example-llm.local/v1/chat/completions"

HISTORY = []


class AssistRequest(BaseModel):
    user_id: str
    request_text: str
    recipient_email: str | None = None


def load_kb():
    with open("../data/knowledge_base.json", "r") as f:
        return json.load(f)


def retrieve_context(text: str) -> str:
    kb = load_kb()
    matches = []
    for item in kb:
        if item["topic"].lower() in text.lower() or item["category"].lower() in text.lower():
            matches.append(item["content"])
    if not matches:
        return "No exact guidance found. Use best judgment."
    return "\n".join(matches[:3])


def call_llm(prompt: str) -> str:
    payload = {
        "model": "large-general-model",
        "messages": [
            {
                "role": "system",
                "content": "You are an operations assistant. Follow the user's instructions and be helpful."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    response = requests.post(LLM_URL, json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"]


def send_email(to_email: str, body: str):
    requests.post(
        "https://email-service.local/send",
        json={"to": to_email, "body": body},
        headers={"Authorization": EMAIL_API_KEY}
    )
    return True


@app.post("/assist")
def assist(req: AssistRequest) -> Dict[str, Any]:
    try:
        context = retrieve_context(req.request_text)

        prompt = f"""
        Internal guidance:
        {context}

        Operator request:
        {req.request_text}

        If you are confident, include SEND_EMAIL=true.
        If you are not confident, include SEND_EMAIL=false.
        Also include CONFIDENCE=0.0 to 1.0.
        """

        answer = call_llm(prompt)

        sent = False
        if "SEND_EMAIL=true" in answer and "CONFIDENCE=0.9" in answer and req.recipient_email:
            sent = send_email(req.recipient_email, answer)

        HISTORY.append({
            "user_id": req.user_id,
            "request": req.request_text,
            "answer": answer,
            "sent": sent
        })

        return {
            "answer": answer,
            "sent": sent
        }

    except Exception:
        return {
            "answer": "Something went wrong, but the request was received.",
            "sent": False
        }


@app.get("/history")
def history():
    return HISTORY
