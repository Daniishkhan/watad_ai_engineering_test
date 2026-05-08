# Design Proposal Under Review

Author: Junior Engineer  
Status: Ready for review  
Target release: Internal pilot

## Summary

I propose building an Internal Operations Assistant using FastAPI and an LLM. The assistant will receive text from the operator, retrieve relevant internal knowledge, ask the LLM what to do, and return a message.

If the LLM says the request is high confidence, the assistant can send the message directly to the supplier or applicant.

## Proposed architecture

```text
Operator UI
   |
   v
FastAPI /assist endpoint
   |
   v
Load knowledge_base.json
   |
   v
Concatenate user request + retrieved guidance
   |
   v
Call LLM
   |
   v
Return response
   |
   v
If confidence > 0.8, send email automatically
```

## Components

### FastAPI service

One endpoint:

`POST /assist`

Input:

```json
{
  "user_id": "ops-123",
  "request_text": "Summarize this RFQ and contact the supplier",
  "recipient_email": "supplier@example.com"
}
```

Output:

```json
{
  "answer": "The supplier should be contacted...",
  "sent": true
}
```

### Retrieval

Retrieval will search the knowledge base file using keyword matching.

The retrieval result is added to the prompt.

If no result is found, the assistant will still ask the LLM to produce the best possible response.

### LLM behavior

The LLM will decide:

- summary
- extracted fields
- next action
- confidence
- whether to send an email

### Email sending

If the LLM response contains `SEND_EMAIL=true` and confidence is above 0.8, the service will send the email directly.

This is useful because it reduces manual work.

### Error handling

If any error happens, the API will return a generic message and continue.

### Logging

Basic print statements are enough for the pilot.

### Permissions

The endpoint is internal, so detailed permissions can be added later.

### Audit log

The response text can be used as a record for now.

### Evaluation

We will manually check outputs during pilot.

### Future improvements

- Add a database.
- Add better search.
- Add more tests.
- Add monitoring if the pilot succeeds.
