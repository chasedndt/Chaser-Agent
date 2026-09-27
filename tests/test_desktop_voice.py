"""Desktop push-to-talk stays explicit, bounded and draft-only."""

import threading
import time
from pathlib import Path

from chaser_agent.desktop_voice import DesktopVoiceController
from chaser_agent.local_stt import CaptureCancelled


def test_model_load_does_not_open_microphone_and_click_returns_draft(tmp_path: Path):
    ready = threading.Event()
    drafted = threading.Event()
    events = []
    recordings = []

    class FakeTranscriber:
        def transcribe(self, pcm):
            assert pcm == b"toy pcm"
            return {"status": "draft_unverified", "text": "What's your status?",
                    "authority": "transcript_only_no_dispatch"}

    def on_event(event, payload):
        events.append((event, payload))
        if event == "ready":
            ready.set()
        if event == "draft":
            drafted.set()

    def recorder(seconds, *, cancel_event):
        recordings.append(seconds)
        assert not cancel_event.is_set()
        return b"toy pcm"

    controller = DesktopVoiceController(
        model_dir=tmp_path, on_event=on_event,
        transcriber_factory=lambda _path: FakeTranscriber(), recorder=recorder,
    )
    controller.start()
    assert ready.wait(2)
    assert recordings == []
    assert controller.capture()
    assert drafted.wait(2)
    assert recordings == [5.0]
    assert events[-1][1]["authority"] == "transcript_only_no_dispatch"
    controller.close()


def test_cancel_discards_take_and_close_stops_capture(tmp_path: Path):
    ready = threading.Event()
    recording_started = threading.Event()
    cancelled = threading.Event()
    transcribed = []

    class FakeTranscriber:
        def transcribe(self, _pcm):
            transcribed.append(True)
            return {"status": "draft_unverified", "text": "must not appear"}

    def recorder(_seconds, *, cancel_event):
        recording_started.set()
        while not cancel_event.is_set():
            time.sleep(0.01)
        raise CaptureCancelled("discarded")

    def on_event(event, _payload):
        if event == "ready":
            ready.set()
        if event == "cancelled":
            cancelled.set()

    controller = DesktopVoiceController(
        model_dir=tmp_path, on_event=on_event,
        transcriber_factory=lambda _path: FakeTranscriber(), recorder=recorder,
    )
    controller.start()
    assert ready.wait(2)
    assert controller.capture()
    assert recording_started.wait(2)
    controller.cancel()
    assert cancelled.wait(2)
    assert not transcribed
    recording_started.clear()
    assert controller.capture()
    assert recording_started.wait(2)
    controller.close()
    assert not transcribed


def test_model_failure_keeps_microphone_inactive(tmp_path: Path):
    unavailable = threading.Event()

    def broken_model(_path):
        raise ValueError("invalid model")

    controller = DesktopVoiceController(
        model_dir=tmp_path, on_event=lambda event, _payload: unavailable.set() if event == "model_unavailable" else None,
        transcriber_factory=broken_model,
    )
    controller.start()
    assert unavailable.wait(2)
    assert not controller.capture()
    controller.close()


def test_failed_recording_indicator_prevents_microphone_open(tmp_path: Path):
    ready = threading.Event()
    recordings = []

    class FakeTranscriber:
        pass

    def on_event(event, _payload):
        if event == "ready":
            ready.set()
        if event == "recording":
            raise RuntimeError("the indicator could not be displayed")

    def recorder(_seconds, *, cancel_event):
        recordings.append(True)
        return b"pcm"

    controller = DesktopVoiceController(
        model_dir=tmp_path, on_event=on_event,
        transcriber_factory=lambda _path: FakeTranscriber(), recorder=recorder,
    )
    controller.start()
    assert ready.wait(2)
    assert not controller.capture()
    assert recordings == []
    controller.close()
