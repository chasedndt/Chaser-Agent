"""Thread-safe HUD read model for a future authenticated computer-use adapter.

No HTTP route can create a computer-use session or send a control command.
Only a separately authorized in-process executor integration may call the
mutation methods. This registry is presentation state, not execution authority.
"""

from dataclasses import asdict
from threading import Lock

from chaser_agent.hud import HudState
from chaser_agent.hud_controls import ControlState, disconnect, receive_status, request_control


class HudRegistry:
    def __init__(self):
        self._lock = Lock()
        self._state: ControlState | None = None

    def begin_session(self, session_id: str) -> None:
        if not session_id.strip():
            raise ValueError("A session ID is required")
        with self._lock:
            if self._state is not None and self._state.hud.phase not in {"completed", "failed", "stopped"}:
                raise ValueError("An active HUD session already exists")
            self._state = ControlState(HudState(session_id))

    def receive_event(self, *, session_id: str, sequence: int, phase: str,
                      action: str = "", request_id: str | None = None,
                      accepted: bool = True) -> None:
        if len(action) > 160:
            raise ValueError("HUD action summary is too long")
        with self._lock:
            if self._state is None:
                raise ValueError("No HUD session exists")
            self._state = receive_status(
                self._state, session_id=session_id, sequence=sequence, phase=phase,
                request_id=request_id, accepted=accepted, action=action,
            )

    def request_control(self, *, request_id: str, command: str) -> None:
        """Record a pending request; an executor adapter must separately dispatch it."""
        with self._lock:
            if self._state is None:
                raise ValueError("No HUD session exists")
            self._state = request_control(self._state, request_id, command)

    def disconnect(self) -> None:
        with self._lock:
            if self._state is not None and self._state.hud.phase not in {"completed", "failed", "stopped"}:
                self._state = disconnect(self._state)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            state = self._state
            if state is None:
                return {
                    "status": "inactive", "session_id": None, "phase": None,
                    "connected": False, "controls_enabled": False,
                    "authority": "display_only_no_executor",
                }
            snapshot = asdict(state)
        return {
            "status": "session_observed" if snapshot["hud"]["phase"] is not None else "awaiting_first_event",
            "session_id": snapshot["hud"]["session_id"],
            "sequence": snapshot["hud"]["sequence"],
            "phase": snapshot["hud"]["phase"],
            "action": snapshot["hud"]["action"],
            "connected": snapshot["connected"],
            "pending_id": snapshot["pending_id"],
            "pending_command": snapshot["pending_command"],
            "notice": snapshot["notice"],
            "controls_enabled": False,
            "authority": "display_only_no_executor",
        }
