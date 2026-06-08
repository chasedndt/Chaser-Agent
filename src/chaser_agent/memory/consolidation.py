MEMORY_STATES=["raw context","candidate memory","reviewed memory","promoted memory","stale memory","disputed memory","archived memory","rejected memory"]

def next_review_state(current: str) -> str:
    if current == "raw context":
        return "candidate memory"
    if current == "candidate memory":
        return "reviewed memory"
    return current
