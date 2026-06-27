STATUS_MAP = {
    "approved": "approved",
    "pending": "pending",
    "in_process": "pending",
    "rejected": "rejected",
    "cancelled": "cancelled",
    "refunded": "refunded",
    "charged_back": "charged_back",
}

ALLOWED_TRANSITIONS = {
    "created": {"preference_created", "pending", "approved", "rejected", "error", "manual_review"},
    "preference_created": {
        "pending",
        "approved",
        "rejected",
        "cancelled",
        "manual_review",
        "error",
    },
    "pending": {"approved", "rejected", "cancelled", "manual_review"},
    "approved": {"refunded", "charged_back", "manual_review"},
    "rejected": set(),
    "cancelled": set(),
    "refunded": set(),
    "charged_back": set(),
    "error": {"preference_created", "manual_review"},
    "manual_review": set(),
}


def mp_status_to_internal(status: str | None) -> str:
    return STATUS_MAP.get(status or "", "manual_review")


def can_transition(current_status: str, new_status: str) -> bool:
    if current_status == new_status:
        return True
    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())
