from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_assist_returns_answer():
    response = client.post("/assist", json={
        "user_id": "ops-123",
        "request_text": "Summarize the RFQ for concrete and prepare supplier message.",
        "recipient_email": "supplier@example.com"
    })

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "sent" in body
