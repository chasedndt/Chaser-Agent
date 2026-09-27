import pytest

from chaser_agent.hud import HudState, apply_status
from chaser_agent.hud_controls import ControlState, disconnect, receive_status, request_control
from chaser_agent.hud_runtime import HudBridge, HudRegistry, HudUnavailable
from chaser_agent.local_acl import InsecureRuntimePath


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


class RecordingExecutor:
    def __init__(self):
        self.requests = []

    def request_control(self, command, request_id):
        self.requests.append((command, request_id))


def test_bridge_requires_attached_executor_and_matching_ack():
    bridge = HudBridge()
    with pytest.raises(HudUnavailable):
        bridge.request_control(session_id="s", request_id="r0", command="stop")
    executor = RecordingExecutor()
    report = bridge.attach("s", executor)
    report(sequence=0, phase="running", action="Reviewing toy page")
    assert bridge.snapshot()["available_controls"] == ["pause", "stop", "take_over"]
    with pytest.raises(HudUnavailable):
        bridge.request_control(session_id="foreign", request_id="r1", command="pause")
    pending = bridge.request_control(session_id="s", request_id="r1", command="pause")
    assert executor.requests == [("pause", "r1")]
    assert pending["phase"] == "running" and pending["pending_id"] == "r1"
    report(sequence=1, phase="paused", request_id="other")
    assert bridge.snapshot()["phase"] == "running"
    report(sequence=1, phase="paused", request_id="r1")
    assert bridge.snapshot()["phase"] == "paused"
    bridge.detach()
    assert bridge.snapshot()["controls_enabled"] is False
    with pytest.raises(HudUnavailable):
        report(sequence=2, phase="running")


def test_bridge_dispatch_failure_preserves_unknown_execution_state():
    class FailingExecutor:
        def request_control(self, command, request_id):
            raise RuntimeError("transport failed")

    bridge = HudBridge()
    report = bridge.attach("s", FailingExecutor())
    report(sequence=0, phase="running")
    with pytest.raises(HudUnavailable):
        bridge.request_control(session_id="s", request_id="r1", command="stop")
    state = bridge.snapshot()
    assert state["phase"] == "running" and state["connected"] is False
    assert state["pending_id"] == "r1" and state["controls_enabled"] is False


def test_only_original_executor_reconnects_uncertain_session_with_fresh_event():
    bridge = HudBridge()
    owner = RecordingExecutor()
    old_report = bridge.attach("s", owner)
    old_report(sequence=0, phase="running", action="Toy task")
    bridge.request_control(session_id="s", request_id="pause-1", command="pause")
    bridge.detach()
    uncertain = bridge.snapshot()
    assert uncertain["phase"] == "running" and uncertain["connected"] is False
    assert uncertain["pending_id"] == "pause-1" and not uncertain["controls_enabled"]
    with pytest.raises(HudUnavailable, match="original executor"):
        bridge.attach("s", RecordingExecutor())
    with pytest.raises(HudUnavailable, match="original executor"):
        bridge.attach("other", owner)
    report = bridge.attach("s", owner)
    assert not bridge.snapshot()["controls_enabled"]
    with pytest.raises(HudUnavailable):
        old_report(sequence=1, phase="paused", request_id="pause-1")
    report(sequence=1, phase="paused", request_id="pause-1")
    restored = bridge.snapshot()
    assert restored["phase"] == "paused" and restored["connected"] is True
    assert restored["pending_id"] is None and restored["available_controls"] == ["resume", "stop", "take_over"]


def test_terminal_session_can_be_replaced_by_new_executor():
    bridge = HudBridge()
    old_report = bridge.attach("old", RecordingExecutor())
    old_report(sequence=0, phase="stopped")
    bridge.detach()
    new_report = bridge.attach("new", RecordingExecutor())
    new_report(sequence=0, phase="running")
    assert bridge.snapshot()["session_id"] == "new"


def test_bridge_accepts_immediate_ack_and_rejects_missing_executor_contract():
    bridge = HudBridge()
    with pytest.raises(ValueError):
        bridge.attach("s", object())

    class ImmediateExecutor:
        def request_control(self, command, request_id):
            report(sequence=1, phase="paused", request_id=request_id)

    report = bridge.attach("s", ImmediateExecutor())
    report(sequence=0, phase="running")
    result = bridge.request_control(session_id="s", request_id="r1", command="pause")
    assert result["phase"] == "paused" and result["pending_id"] is None


def test_normal_hud_refuses_broad_token_before_opening_window(tmp_path, monkeypatch):
    from chaser_agent.hud_window import HudWindow

    def reject(_path):
        raise InsecureRuntimePath("broad ACL")

    monkeypatch.setattr("chaser_agent.hud_window.read_private_control_token", reject)
    with pytest.raises(InsecureRuntimePath, match="broad ACL"):
        HudWindow(token_file=tmp_path / "control-token")


def test_desktop_idle_hud_stays_visible_with_port_and_disabled_controls():
    from chaser_agent.hud_window import HudWindow

    class FakeLabel:
        def __init__(self):
            self.values = {}

        def configure(self, **kwargs):
            self.values.update(kwargs)

    class FakeRoot:
        def __init__(self):
            self.shown = False

        def deiconify(self):
            self.shown = True

    window = object.__new__(HudWindow)
    window.preview = False
    window.show_idle = True
    window.port = 8765
    window._visible = False
    window._current_session = "old-session"
    window.root = FakeRoot()
    window.buttons = {"pause": FakeLabel(), "stop": FakeLabel()}
    window.phase_label = FakeLabel()
    window.action_label = FakeLabel()
    window.session_label = FakeLabel()
    window.notice_label = FakeLabel()
    window._render({"status": "inactive"})
    assert window.root.shown and window._visible
    assert window._current_session is None
    assert window.phase_label.values["text"] == "Local service ready"
    assert window.session_label.values["text"] == "Local API 127.0.0.1:8765"
    assert all(button.values["state"] == "disabled" for button in window.buttons.values())


def test_voice_panel_only_enables_status_speech_for_exact_draft():
    from chaser_agent.hud_window import HudWindow

    class FakeWidget:
        def __init__(self):
            self.values = {}

        def configure(self, **kwargs):
            self.values.update(kwargs)

    window = object.__new__(HudWindow)
    window._closed = False
    window.voice_output_enabled = True
    window._voice_draft = None
    window.talk_button = FakeWidget()
    window.speak_button = FakeWidget()
    window.clear_button = FakeWidget()
    window.voice_state_label = FakeWidget()
    window.voice_draft_label = FakeWidget()
    window._on_voice_event("draft", {"text": "Stop the computer", "status": "draft_unverified"})
    assert window.speak_button.values["state"] == "disabled"
    assert window.clear_button.values["state"] == "normal"
    window._on_voice_event("draft", {"text": "What's your status?", "status": "draft_unverified"})
    assert window.speak_button.values["state"] == "normal"
    assert "unverified" in window.voice_draft_label.values["text"]
    window._on_voice_event("recording", None)
    assert window.talk_button.values["text"] == "Cancel take"
    assert window.speak_button.values["state"] == "disabled"


def test_voice_panel_ignores_stale_draft_and_cancel_after_new_take_starts():
    from chaser_agent.hud_window import HudWindow

    class FakeWidget:
        def __init__(self):
            self.values = {}

        def configure(self, **kwargs):
            self.values.update(kwargs)

    window = object.__new__(HudWindow)
    window._closed = False
    window.voice_output_enabled = True
    window._voice_draft = None
    window._active_capture_id = None
    window.talk_button = FakeWidget()
    window.speak_button = FakeWidget()
    window.clear_button = FakeWidget()
    window.voice_state_label = FakeWidget()
    window.voice_draft_label = FakeWidget()
    window._on_voice_event("recording", {"capture_id": 2})
    window._on_voice_event("draft", {
        "capture_id": 1, "status": "draft_unverified", "text": "What's your status?",
    })
    window._on_voice_event("cancelled", {"capture_id": 1})
    assert window._voice_draft is None
    assert window.talk_button.values["text"] == "Cancel take"
    assert window.speak_button.values["state"] == "disabled"
    assert window.voice_state_label.values["text"].startswith("MICROPHONE ACTIVE")
    window._on_voice_event("draft", {
        "capture_id": 2, "status": "draft_unverified", "text": "What's your status?",
    })
    assert window._voice_draft == "What's your status?"
    assert window.speak_button.values["state"] == "normal"


def test_voice_panel_cancel_reply_requires_separate_click_and_blocks_talk(monkeypatch):
    import threading
    from chaser_agent.hud_window import HudWindow

    class FakeWidget:
        def __init__(self):
            self.values = {}

        def configure(self, **kwargs):
            self.values.update(kwargs)

    class FakeThread:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def start(self):
            pass

    class FakeController:
        def is_busy(self):
            return False

    monkeypatch.setattr("chaser_agent.hud_window.threading.Thread", FakeThread)
    window = object.__new__(HudWindow)
    window._closed = False
    window.voice_output_enabled = True
    window._voice_draft = "What's your status?"
    window._speech_busy = False
    window._speech_cancel = threading.Event()
    window._voice_controller = FakeController()
    window.talk_button = FakeWidget()
    window.speak_button = FakeWidget()
    window.voice_state_label = FakeWidget()
    window._voice_speak()
    assert window._speech_busy
    assert not window._speech_cancel.is_set()
    assert window.speak_button.values["text"] == "Cancel reply"
    assert window.talk_button.values["state"] == "disabled"
    window._voice_speak()
    assert window._speech_cancel.is_set()
    assert window.speak_button.values["text"] == "Stopping…"
    window._finish_speech("Reply stop requested")
    assert not window._speech_busy
    assert window.speak_button.values["text"] == "Speak status"
    assert window.talk_button.values["state"] == "normal"


def test_recording_indicator_is_painted_before_microphone_worker_starts():
    import threading
    from chaser_agent.hud_window import HudWindow

    events = []

    class FakeRoot:
        def update_idletasks(self):
            events.append("paint")

    window = object.__new__(HudWindow)
    window._closed = False
    window._ui_thread_id = threading.get_ident()
    window.root = FakeRoot()
    window._on_voice_event = lambda event, _payload: events.append(event)
    window._queue_voice_event("recording", None)
    assert events == ["recording", "paint"]


def test_background_model_ready_event_waits_for_ui_thread():
    import queue
    import threading
    from chaser_agent.hud_window import HudWindow

    events = []

    class FakeRoot:
        def after(self, _delay, _callback):
            events.append("scheduled")

    window = object.__new__(HudWindow)
    window._closed = False
    window._ui_thread_id = threading.get_ident()
    window._voice_events = queue.Queue()
    window.root = FakeRoot()
    window._on_voice_event = lambda event, _payload: events.append(event)
    worker = threading.Thread(target=window._queue_voice_event, args=("ready", None))
    worker.start()
    worker.join(timeout=2)
    assert events == []
    window._drain_voice_events()
    assert events == ["ready", "scheduled"]


def test_hud_dimensions_scale_and_cap_to_available_screen():
    from chaser_agent.hud_window import hud_dimensions

    assert hud_dimensions(tk_scale=1.333, screen_width=1920,
                          screen_height=1080, voice_panel=True) == (410, 452, 350)
    assert hud_dimensions(tk_scale=2.666, screen_width=1920,
                          screen_height=1080, voice_panel=True) == (820, 904, 760)
    assert hud_dimensions(tk_scale=2.666, screen_width=800,
                          screen_height=600, voice_panel=True) == (760, 520, 700)
