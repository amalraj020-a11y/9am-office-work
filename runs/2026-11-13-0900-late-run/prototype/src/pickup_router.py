"""Synthetic-data pickup request router for Viva Laundry."""
from dataclasses import asdict, dataclass
import json, sys

AREA_BRANCH = {
    "carmelaram": "Carmelaram", "mullur": "Carmelaram", "kodathi gate": "Carmelaram",
    "ambedkar nagar": "Ambedkar Nagar", "sarjapur road": "Ambedkar Nagar",
    "attibele": "Attibele", "sarjapura": "Attibele",
}
SERVICES = {"ironing", "washing and folding", "washing and ironing", "dry cleaning", "shoe cleaning", "saree rolling"}

@dataclass
class PickupDecision:
    branch: str | None
    service: str | None
    priority: str
    missing_fields: list[str]
    route: str
    draft_reply: str

def route_pickup(request: dict) -> PickupDecision:
    area = str(request.get("area", "")).strip().lower()
    service = str(request.get("service", "")).strip().lower()
    notes = str(request.get("notes", "")).lower()
    branch = AREA_BRANCH.get(area)
    missing = [f for f in ("name", "phone", "pickup_slot") if not request.get(f)]
    if not area: missing.append("area")
    elif branch is None: missing.append("service_area_confirmation")
    if not service: missing.append("service")
    elif service not in SERVICES: missing.append("service_confirmation")
    express = any(t in notes for t in ("urgent", "express", "same day", "today"))
    route = "request_missing_information" if missing else "express_availability_review" if express else "standard_pickup_confirmation"
    reply = "Please provide or confirm: " + ", ".join(missing) + "." if missing else f"Your request is ready for {branch} branch pickup confirmation."
    return PickupDecision(branch, service or None, "high" if express else "normal", missing, route, reply)

if __name__ == "__main__":
    print(json.dumps(asdict(route_pickup(json.loads(sys.stdin.read() or "{}"))), indent=2))
