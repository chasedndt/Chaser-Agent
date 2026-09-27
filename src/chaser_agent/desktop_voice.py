"""Opt-in, cancellable microphone-to-draft controller for the local HUD.

No microphone opens until capture() is called by a visible button. Transcripts
remain drafts in memory; this controller has no action or provider dispatch.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from chaser_agent.local_stt import CaptureCancelled, OfflineTranscriber, record_once

VoiceEvent = Callable[[str, dict[str, object] | None], None]


class DesktopVoiceController:
    def __init__(self, *, model_dir: Path, on_event: VoiceEvent,
                 seconds: float = 5.0, transcriber_factory=OfflineTranscriber,
                 recorder=record_once):
        if not 0.5 <= seconds <= 12:
            raise ValueError("Voice capture must be 0.5–12 seconds")
        self.model_dir = model_dir
        self.on_event = on_event
        self.seconds = seconds
        self._transcriber_factory = transcriber_factory
        self._recorder = recorder
        self._lock = threading.Lock()
        self._closed = False
        self._started = False
        self._busy = False
        self._transcriber = None
        self._cancel = threading.Event()
        self._capture_thread: threading.Thread | None = None

    def _emit(self, event: str, payload: dict[str, object] | None = None) -> bool:
        with self._lock:
            if self._closed:
                return False
        try:
            self.on_event(event, payload)
            return True
        except Exception:
            return False

    def start(self) -> None:
        with self._lock:
            if self._closed or self._started:
                return
            self._started = True
        self._emit("loading")
        threading.Thread(target=self._load, name="chaser-local-stt-load", daemon=True).start()

    def _load(self) -> None:
        try:
            transcriber = self._transcriber_factory(self.model_dir)
        except Exception:
            self._emit("model_unavailable")
            return
        with self._lock:
            if self._closed:
                return
            self._transcriber = transcriber
        self._emit("ready")

    def capture(self) -> bool:
        with self._lock:
            if self._closed or self._transcriber is None or self._busy:
                return False
            self._busy = True
            self._cancel = threading.Event()
            cancel = self._cancel
            transcriber = self._transcriber
        if not self._emit("recording"):
            with self._lock:
                self._busy = False
            return False
        worker = threading.Thread(
            target=self._capture, args=(cancel, transcriber),
            name="chaser-explicit-microphone-take", daemon=True,
        )
        self._capture_thread = worker
        worker.start()
        return True

    def _capture(self, cancel: threading.Event, transcriber) -> None:
        event = "cancelled"
        payload = None
        try:
            pcm = self._recorder(self.seconds, cancel_event=cancel)
            if cancel.is_set():
                raise CaptureCancelled("Microphone take cancelled")
            self._emit("transcribing")
            result = transcriber.transcribe(pcm)
            if cancel.is_set():
                raise CaptureCancelled("Voice draft discarded")
            if result.get("status") == "draft_unverified":
                event, payload = "draft", result
            elif result.get("status") == "no_speech":
                event = "no_speech"
            else:
                event = "transcription_unavailable"
        except CaptureCancelled:
            event = "cancelled"
        except Exception:
            event = "transcription_unavailable"
        finally:
            with self._lock:
                self._busy = False
            self._emit(event, payload)

    def cancel(self) -> None:
        with self._lock:
            if not self._busy:
                return
            self._cancel.set()
        self._emit("cancelling")

    def is_busy(self) -> bool:
        with self._lock:
            return self._busy

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._cancel.set()
            worker = self._capture_thread
        if worker is not None and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout=2)
