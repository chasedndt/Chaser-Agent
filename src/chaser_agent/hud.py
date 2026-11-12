"""Display state for one computer-use session; never executes or approves work."""

from dataclasses import dataclass, replace
from typing import Literal

HudPhase = Literal["running", "awaiting_approval", "paused", "completed", "failed", "stopped"]


@dataclass(frozen=True)
class HudState:
    session_id: str
    sequence: int = -1
    phase: HudPhase | None = None
    action: str = ""

    @property
    def visible(self) -> bool:
        return self.phase is not None


def apply_status(state: HudState, *, session_id: str, sequence: int,
                 phase: HudPhase, action: str = "") -> HudState:
    """Apply ordered adapter status; ignore stale or foreign-session events."""
    if phase not in {"running", "awaiting_approval", "paused", "completed", "failed", "stopped"}:
        raise ValueError("Unknown HUD phase")
    if not state.session_id or not session_id or type(sequence) is not int or sequence < 0:
        raise ValueError("A session identity and nonnegative integer sequence are required")
    if session_id != state.session_id or sequence <= state.sequence:
        return state
    if state.phase in {"completed", "failed", "stopped"}:
        return state
    return replace(state, sequence=sequence, phase=phase, action=action)
