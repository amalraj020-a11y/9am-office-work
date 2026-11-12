# Amala Codex + OpenClaw controlled test — 2026-11-12

## Business and evidence

- Business: HandyMan Service India
- Official website: https://handymanservice.in/
- Public business email: info@handymanservice.in
- Verified public evidence: the official site lists multiple home, office, care, vehicle, taxi, and driver services. Its published workflow asks for service needs, location, preferred time, and work details, followed by team review of requirements, availability, and a suitable professional.
- Evidence file: `evidence.md`

## Problem hypothesis

Because the business offers many service categories and publicly describes a team review step, incoming booking requests may require repetitive first-pass checking for service category, urgency, city or area, preferred time, and missing contact details. This is a hypothesis to validate with the business, not a claimed fact.

## Proposed solution

A human-reviewed booking-triage assistant:

- Inputs: name, mobile, email, city or area, preferred time, and service message.
- Processing: required-field validation, service classification, urgency detection, priority scoring, and routing.
- Outputs: structured booking, missing-field checklist, priority score, queue route, and a draft customer reply.
- Expected value: faster, more consistent first-pass review while keeping availability, professional assignment, pricing, and final communication under human control.
- Limitations: synthetic data only; no production integration, pricing decision, professional assignment, or customer-data access.

## Prototype and tests

- Prototype: `prototype/src/triage.py`
- Test suite: `prototype/tests/test_triage.py`
- Result: **PASS — 4/4 tests**
- Synthetic urgent-electrician example: classified as `electrical`, urgency `high`, score `90`, route `urgent_review`.

```text
test_complete_plumbing_booking ... ok
test_missing_information ... ok
test_unknown_service_requests_details ... ok
test_urgent_request ... ok
Ran 4 tests in 0.003s — OK
```

## Models and infrastructure

- Orchestrator: OpenAI Codex
- OpenClaw gateway: PASS (`live`)
- Ollama primary: `qwen3:4b` ran, but its short review was incomplete.
- Ollama fallback: `gemma3:1b` completed the independent local review.
- Local review: “The core problem is a hypothesis—repetitive manual triage across numerous services, locations, times, and fields. Validation, classification, and prioritization could streamline operations.”
- Actual paid API cost: **₹0**

## Outreach draft

Subject: Idea to streamline HandyMan Service India booking requests

Hello HandyMan Service India team,

I reviewed the booking process and range of services published on your official website. A possible opportunity—subject to your confirmation—is reducing repetitive first-pass checks across service type, urgency, city or area, preferred time, and missing contact details.

Multimax prepared a small booking-triage prototype using synthetic data only. It validates required fields, classifies the requested service and urgency, creates a priority score, and prepares a draft reply for human review. Availability, pricing, professional assignment, and final customer communication remain under your team’s control.

If this is relevant, we would be happy to share a short demonstration. No access to customer data is needed for the initial demo.

Regards,
Amala
Multimax

## Outreach status

- Gmail profile verified: `amalaraj020@gmail.com`
- Duplicate Sent/Draft search: no matching message found before draft creation.
- Gmail draft creation: **PASS** (`DRAFT` label verified).
- Gmail sending: **PASS** — sent to the verified public business address and confirmed with Gmail's `SENT` label.
- Authorization: standing approval now permits verified initial outreach after duplicate checks; commercial proposals and commitments remain approval-controlled.
