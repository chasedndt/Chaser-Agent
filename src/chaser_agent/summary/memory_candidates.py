from chaser_agent.schemas import MemoryCandidate

def extract_memory_candidates(text: str) -> list[MemoryCandidate]:
    if "memory" not in text.lower() and "remember" not in text.lower():
        return []
    return [MemoryCandidate(text="Review possible durable memory signal.", evidence=text[:240])]
