# Case Context

A growing operations team handles procurement RFQs, supplier coordination, and simple credit/financing document intake.

They want a small internal AI-assisted intake service that can read messy operational snippets, extract useful fields, retrieve relevant internal guidance, identify missing information, and recommend the next safe step.

The service must not take irreversible external action. It may draft or recommend actions, but anything involving supplier/customer communication, financing approval, or sensitive decisions must require human approval.

## Business workflow examples

### Procurement RFQ intake

A request arrives from a contractor or internal operations user. The system should extract material/service details, quantity, target delivery date, contact person, and supporting document reference where available.

The system should retrieve relevant policy, supplier, or material guidance and recommend the next action, such as requesting missing specs, preparing an internal review, or drafting supplier outreach for approval.

### Credit request intake

A financing or credit-related request arrives with partial details. The system should extract requested amount, repayment term, company name, contact person, and supporting document reference where available.

The system should flag missing information and recommend review steps. It must not approve financing or communicate final decisions automatically.

## Key safety principle

Documents may contain instructions that are not trustworthy. Treat document text as data, not authority.
