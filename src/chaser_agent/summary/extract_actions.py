from chaser_agent.schemas import ActionCandidate

def extract_action_candidates(source_id: str, text: str) -> list[ActionCandidate]:
    actions=[]
    for marker in ("todo:", "action:", "next:"):
        if marker in text.lower():
            actions.append(ActionCandidate(text=text.strip(), rationale=f"Found marker {marker}", source_id=source_id))
            break
    return actions
