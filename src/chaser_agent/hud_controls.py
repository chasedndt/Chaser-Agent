"""In-memory control handshake for an adapter-driven HUD, without dispatch."""

from dataclasses import dataclass, replace

from chaser_agent.hud import HudState, apply_status

TARGETS = {"pause": "paused", "resume": "running", "stop": "stopped", "take_over": "stopped"}


@dataclass(frozen=True)
class ControlState:
    hud: HudState
    connected: bool = True
    pending_id: str | None = None
    pending_command: str | None = None
    used_ids: tuple[str, ...] = ()
    notice: str = ""


def request_control(state: ControlState, request_id: str, command: str) -> ControlState:
    if command not in TARGETS or not request_id.strip():
        raise ValueError("A supported command and request ID are required")
    if request_id in state.used_ids:
        raise ValueError("Request ID was already used")
    if not state.connected or state.hud.phase in {None, "completed", "failed", "stopped"}:
        raise ValueError("No connected active session")
    if state.pending_id and command not in {"stop", "take_over"}:
        raise ValueError("A control request is pending")
    if command == "resume" and state.hud.phase != "paused":
        raise ValueError("Only a paused session can resume")
    return replace(state, pending_id=request_id, pending_command=command,
                   used_ids=state.used_ids + (request_id,), notice="Awaiting executor acknowledgement")


def disconnect(state: ControlState) -> ControlState:
    return replace(state, connected=False, notice="Connection lost; execution status unknown")


def receive_status(state: ControlState, *, session_id: str, sequence: int,
                   phase: str, request_id: str | None = None,
                   accepted: bool = True, action: str = "") -> ControlState:
    """Only matching, newer acknowledgements settle a pending control.

    Adapter authentication and transport are separate integration responsibilities.
    Ordinary status events cannot clear a pending request unless execution ends.
    """
    if session_id != state.hud.session_id or sequence <= state.hud.sequence:
        return state
    if request_id is not None:
        if request_id != state.pending_id:
            return state
        if accepted and phase != TARGETS[state.pending_command]:
            raise ValueError("Acknowledgement does not match the requested outcome")
    hud = apply_status(state.hud, session_id=session_id, sequence=sequence,
                       phase=phase, action=action)
    if hud == state.hud:
        return state
    settled = request_id is not None or phase in {"completed", "failed", "stopped"}
    return replace(state, hud=hud, connected=True,
                   pending_id=None if settled else state.pending_id,
                   pending_command=None if settled else state.pending_command,
                   notice=("Executor rejected the request" if request_id and not accepted
                           else "" if settled else state.notice))
