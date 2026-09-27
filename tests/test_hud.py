import pytest

from chaser_agent.hud import HudState, apply_status
from chaser_agent.hud_controls import ControlState, disconnect, receive_status, request_control
from chaser_agent.hud_runtime import HudRegistry


def test_hud_appears_on_activity_and_keeps_terminal_receipt():
    initial = HudState("session-a")
    assert not initial.visible
    active = apply_status(initial, session_id="session-a", sequence=0, phase="running")
    assert active.visible
    stopped = apply_status(active, session_id="session-a", sequence=2, phase="stopped")
    assert stopped.visible
    assert apply_status(stopped, session_id="session-a", sequence=3, phase="running") == stopped


def test_stale_and_foreign_events_cannot_change_display():
    state = apply_status(HudState("a"), session_id="a", sequence=4, phase="awaiting_approval")
    assert apply_status(state, session_id="b", sequence=5, phase="completed") == state
    assert apply_status(state, session_id="a", sequence=4, phase="completed") == state


def test_control_waits_for_matching_newer_acknowledgement():
    active = ControlState(HudState("a", 0, "running"))
    pending = request_control(active, "p1", "pause")
    assert pending.hud.phase == "running"
    assert receive_status(pending, session_id="a", sequence=1, phase="paused", request_id="other") == pending
    acknowledged = receive_status(pending, session_id="a", sequence=1, phase="paused", request_id="p1")
    assert acknowledged.hud.phase == "paused" and acknowledged.pending_id is None
    with pytest.raises(ValueError):
        request_control(acknowledged, "p1", "resume")


def test_stop_supersedes_pause_and_disconnect_preserves_uncertainty():
    active = ControlState(HudState("a", 0, "running"))
    pending = request_control(request_control(active, "p", "pause"), "s", "stop")
    assert receive_status(pending, session_id="a", sequence=1, phase="paused", request_id="p") == pending
    disconnected = disconnect(pending)
    assert not disconnected.connected and disconnected.pending_id == "s"
    with pytest.raises(ValueError):
        request_control(disconnected, "r", "resume")
    stopped = receive_status(disconnected, session_id="a", sequence=2, phase="stopped", request_id="s")
    assert stopped.hud.phase == "stopped" and stopped.connected


def test_registry_read_model_remains_non_authoritative():
    registry = HudRegistry()
    assert registry.snapshot()["status"] == "inactive"
    registry.begin_session("demo")
    registry.receive_event(session_id="demo", sequence=0, phase="running", action="Review evidence")
    registry.request_control(request_id="pause-1", command="pause")
    pending = registry.snapshot()
    assert pending["phase"] == "running" and pending["pending_command"] == "pause"
    assert pending["controls_enabled"] is False
    assert pending["authority"] == "display_only_no_executor"
    registry.receive_event(session_id="demo", sequence=1, phase="paused", request_id="pause-1")
    assert registry.snapshot()["phase"] == "paused"
    registry.disconnect()
    assert registry.snapshot()["connected"] is False


def test_registry_rejects_overlong_action_and_overlapping_sessions():
    registry = HudRegistry()
    registry.begin_session("first")
    with pytest.raises(ValueError):
        registry.begin_session("second")
    with pytest.raises(ValueError):
        registry.receive_event(session_id="first", sequence=0, phase="running", action="x" * 161)


def test_terminal_receipt_remains_confirmed_after_transport_disconnect():
    registry = HudRegistry()
    registry.begin_session("done")
    registry.receive_event(session_id="done", sequence=0, phase="running")
    registry.receive_event(session_id="done", sequence=1, phase="stopped")
    registry.disconnect()
    assert registry.snapshot()["phase"] == "stopped"
    assert registry.snapshot()["connected"] is True
