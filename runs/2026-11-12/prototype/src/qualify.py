"""Synthetic-data enquiry qualification prototype."""
from dataclasses import asdict, dataclass
import json
import re
import sys

@dataclass
class Result:
    intent: str
    urgency: str
    city: str | None
    missing_fields: list[str]
    score: int

def qualify(enquiry: dict) -> Result:
    text = str(enquiry.get("message", "")).lower()
    cities = ["delhi", "noida", "gurugram", "gurgaon", "mumbai", "pune", "bengaluru", "bangalore"]
    city = next((c.title() for c in cities if re.search(rf"\b{re.escape(c)}\b", text)), None)
    urgent = any(word in text for word in ("urgent", "today", "asap", "immediately"))
    appointment = any(word in text for word in ("book", "appointment", "visit", "technician"))
    repair = any(word in text for word in ("repair", "screen", "battery", "broken", "not working"))
    intent = "appointment" if appointment else "repair" if repair else "general"
    missing = [key for key in ("name", "contact") if not enquiry.get(key)]
    if city is None:
        missing.append("city")
    score = 50 + (25 if urgent else 0) + (15 if intent != "general" else 0) - 10 * len(missing)
    return Result(intent, "high" if urgent else "normal", city, missing, max(0, min(100, score)))

if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(asdict(qualify(payload)), indent=2))
