"""Thread-safe HUD read model for a future authenticated computer-use adapter.

No HTTP route can create a computer-use session or send a control command.
Only a separately authorized in-process executor integration may call the
mutation methods. This registry is presentation state, not execution authority.
"""

from dataclasses import asdict
from threading import Lock, RLock
from typing import Callable, Protocol

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


class HudExecutor(Protocol):
    """An already-authorized executor; request_control must enqueue promptly."""

    def request_control(self, command: str, request_id: str) -> None: ...


class HudUnavailable(ValueError):
    pass


class HudBridge:
    """Bind one executor's events and acknowledgements to the local HUD.

    HTTP clients cannot attach an executor or publish status. An executor must
    be constructed by a separately governed runtime and attached in process.
    """

    def __init__(self) -> None:
        self.registry = HudRegistry()
        self._lock = RLock()
        self._executor: HudExecutor | None = None
        self._generation = 0

    def attach(self, session_id: str, executor: HudExecutor) -> Callable[..., None]:
        if (not session_id or session_id != session_id.strip() or len(session_id) > 96
                or not callable(getattr(executor, "request_control", None))):
            raise ValueError("A bounded session ID and executor are required")
        with self._lock:
            if self._executor is not None:
                raise HudUnavailable("A HUD executor is already attached")
            self.registry.begin_session(session_id)
            self._generation += 1
            generation = self._generation
            self._executor = executor

        def report(*, sequence: int, phase: str, action: str = "",
                   request_id: str | None = None, accepted: bool = True) -> None:
            with self._lock:
                if generation != self._generation or self._executor is not executor:
                    raise HudUnavailable("This executor attachment is no longer active")
                self.registry.receive_event(
                    session_id=session_id, sequence=sequence, phase=phase,
                    action=action, request_id=request_id, accepted=accepted,
                )

        return report

    def detach(self) -> None:
        with self._lock:
            self._executor = None
            self._generation += 1
            self.registry.disconnect()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            state = self.registry.snapshot()
            attached = self._executor is not None
        phase = state["phase"]
        active = attached and state["connected"] and phase not in {None, "completed", "failed", "stopped"}
        pending = state.get("pending_id") is not None
        available = (["stop", "take_over"] if pending else
                     ["resume", "stop", "take_over"] if phase == "paused" else
                     ["pause", "stop", "take_over"] if phase in {"running", "awaiting_approval"} else [])
        state["controls_enabled"] = bool(active)
        state["available_controls"] = available if active else []
        state["authority"] = "attached_executor_controls" if active else "display_only_no_executor"
        return state

    def request_control(self, *, session_id: str, request_id: str, command: str) -> dict[str, object]:
        with self._lock:
            state = self.registry.snapshot()
            executor = self._executor
            if executor is None or state["session_id"] != session_id or not state["connected"]:
                raise HudUnavailable("No matching connected executor session")
            phase = state["phase"]
            allowed = ({"stop", "take_over"} if state.get("pending_id") else
                       {"resume", "stop", "take_over"} if phase == "paused" else
                       {"pause", "stop", "take_over"} if phase in {"running", "awaiting_approval"} else set())
            if command not in allowed:
                raise HudUnavailable("Control is unavailable in this session state")
            self.registry.request_control(request_id=request_id, command=command)
            try:
                # This call must only enqueue. Holding the reentrant lock stops
                # detach racing a dispatch; same-thread immediate acks can report.
                executor.request_control(command, request_id)
            except Exception:
                # Dispatch may have reached the executor before it failed.
                # Never claim the requested action took effect.
                self.detach()
                raise HudUnavailable("Control dispatch failed; execution status unknown") from None
        return self.snapshot()
