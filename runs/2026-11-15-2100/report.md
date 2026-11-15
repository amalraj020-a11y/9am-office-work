# Amala Office Report — 2026-11-15-2100

- Business: MyKhana
- Official source: https://www.mykhana.in/
- Public email: sales@mykhana.in
- Evidence: official website fetched and identity-checked successfully
- Hypothesis: Catering enquiries may require manual routing by event type, location, date, headcount, menu preference, and budget range. This is a hypothesis to validate with the business.
- Solution: An AI-assisted enquiry qualification workflow that extracts the request type, location, urgency, and missing fields, then produces a structured lead and draft follow-up.
- Inputs: Public website enquiry or booking text, customer name and contact details, requested service, location, and preferred date or slot.
- Processing: Validate required fields, classify intent and urgency, extract service and location, detect missing information, and route the enquiry for follow-up.
- Outputs: A structured lead record, priority score, missing-information checklist, routing suggestion, and draft response for review.
- Expected value: Less manual triage, faster follow-up, more consistent records, and fewer incomplete bookings.
- Model: Ollama qwen3:4b
- OpenClaw: checked by the GitHub workflow before execution
- Prototype: runs/2026-11-15-2100/prototype
- Tests: PASS — 3 automated tests
- Outreach: draft prepared; cloud Gmail credentials are not configured
- Actual paid API cost: ₹0
- Source fallback notes: none

## Draft email

Subject: Idea to streamline MyKhana enquiries

Hello MyKhana team,

I reviewed the enquiry and service information on your public website. A possible opportunity—subject to your confirmation—is automatically sorting incoming requests by service, location, urgency, preferred time, and missing details. Multimax prepared a small prototype using synthetic data only. If useful, I can share a short demonstration.

Regards,
Amala
Multimax

## Test output

```
test_general_enquiry (test_qualify.QualificationTests.test_general_enquiry) ... ok
test_missing_fields (test_qualify.QualificationTests.test_missing_fields) ... ok
test_urgent_booking (test_qualify.QualificationTests.test_urgent_booking) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
```
