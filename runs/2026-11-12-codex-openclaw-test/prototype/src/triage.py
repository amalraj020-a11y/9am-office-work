"""Synthetic-data booking triage prototype for HandyMan Service India."""

from dataclasses import asdict, dataclass
import json
import re
import sys


SERVICE_TERMS = {
    "cleaning": ("clean", "cleaning"),
    "plumbing": ("plumber", "plumbing", "leak", "pipe"),
    "electrical": ("electrician", "electrical", "switch", "wiring"),
    "carpentry": ("carpenter", "carpentry", "furniture"),
    "appliance_repair": ("ac", "appliance", "fridge", "washing machine"),
    "elder_care": ("nurse", "nursing", "elder care", "caregiver"),
    "vehicle_service": ("car wash", "car service", "taxi", "driver"),
}


@dataclass
class TriageResult:
    service: str
    urgency: str
    city: str | None
    preferred_time: str | None
    missing_fields: list[str]
    priority_score: int
    route: str
    draft_reply: str


def triage_booking(booking: dict) -> TriageResult:
    message = str(booking.get("message", "")).strip()
    text = message.lower()

    service = "other"
    for label, terms in SERVICE_TERMS.items():
        if any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms):
            service = label
            break

    urgent = any(term in text for term in ("urgent", "emergency", "today", "immediately", "asap"))
    city = str(booking.get("city", "")).strip() or None
    preferred_time = str(booking.get("preferred_time", "")).strip() or None

    missing = [field for field in ("name", "mobile", "email") if not booking.get(field)]
    if city is None:
        missing.append("city")
    if preferred_time is None:
        missing.append("preferred_time")
    if service == "other":
        missing.append("service_details")

    score = 45 + (30 if urgent else 0) + (15 if service != "other" else 0) - 8 * len(missing)
    score = max(0, min(100, score))
    route = "urgent_review" if urgent else "request_missing_information" if missing else "availability_review"

    if missing:
        draft_reply = "Thank you. Please provide: " + ", ".join(missing) + ". A team member can then review availability and pricing."
    else:
        draft_reply = "Thank you. Your request is ready for availability and pricing review by the service team."

    return TriageResult(
        service=service,
        urgency="high" if urgent else "normal",
        city=city,
        preferred_time=preferred_time,
        missing_fields=missing,
        priority_score=score,
        route=route,
        draft_reply=draft_reply,
    )


if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(asdict(triage_booking(payload)), indent=2))
