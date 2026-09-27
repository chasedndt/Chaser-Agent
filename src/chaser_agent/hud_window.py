"""Small Windows desktop HUD shell driven by authenticated local state.

Controls are only enabled for an attached executor session. A click requests
control; the displayed phase changes only on an executor acknowledgement.
Preview mode is synthetic and never sends a command.
"""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from chaser_agent.local_acl import read_private_control_token
from chaser_agent.hud_runtime import HudRegistry
from chaser_agent.voice_status import status_intent

INK = "#070B14"
PANEL = "#111927"
BONE = "#F4F1EA"
MUTED = "#AAB6C7"
EDGE = "#4EB7FF"
PHASE_COLORS = {
    "running": "#39E6D2",
    "awaiting_approval": "#F0B45A",
    "paused": "#F0B45A",
    "completed": "#F4F1EA",
    "failed": "#FF4D6D",
    "stopped": "#FF4D6D",
}


def hud_dimensions(*, tk_scale: float, screen_width: int,
                   screen_height: int, voice_panel: bool) -> tuple[int, int, int]:
    """Scale the window with text, then cap it to the available display."""
    factor = max(1.0, min(3.0, tk_scale / 1.333))
    width = min(round(410 * factor), max(240, screen_width - 40))
    base_height = 452 if voice_panel else 284
    height = min(round(base_height * factor), max(240, screen_height - 80))
    return width, height, max(180, width - 60)


def fetch_snapshot(*, port: int, token: str) -> dict[str, object]:
    request = Request(
        f"http://127.0.0.1:{port}/v1/hud/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urlopen(request, timeout=2) as response:
        return json.load(response)


def send_control(*, port: int, token: str, session_id: str, command: str) -> dict[str, object]:
    body = json.dumps({"session_id": session_id, "command": command}).encode("utf-8")
    request = Request(
        f"http://127.0.0.1:{port}/v1/hud/controls", data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.load(response)


class HudWindow:
    def __init__(self, *, port: int = 8765, token_file: Path | None = None,
                 preview: bool = False, show_idle: bool = False,
                 voice_model_dir: Path | None = None, voice_output_enabled: bool = False):
        if not preview and token_file is None:
            raise ValueError("A local token file is required outside preview mode")
        self.port = port
        self.token_file = token_file
        self.token = read_private_control_token(token_file.parent) if token_file is not None and not preview else None
        self.preview = preview
        self.show_idle = show_idle
        self.voice_model_dir = voice_model_dir if not preview else None
        self.voice_output_enabled = voice_output_enabled
        self._voice_controller = None
        self._voice_draft: str | None = None
        self._active_capture_id: int | None = None
        self._speech_cancel = threading.Event()
        self._speech_busy = False
        self._barge_in_pending = False
        self._voice_events: queue.Queue[tuple[str, dict[str, object] | None]] = queue.Queue()
        self._ui_thread_id = threading.get_ident()
        self.root = tk.Tk()
        self.root.title("Chaser Agent HUD")
        self.root.configure(bg=INK)
        self._tk_scale = float(self.root.tk.call("tk", "scaling"))
        width, height, self._wrap_length = hud_dimensions(
            tk_scale=self._tk_scale,
            screen_width=self.root.winfo_screenwidth(),
            screen_height=self.root.winfo_screenheight(),
            voice_panel=self.voice_model_dir is not None,
        )
        self.root.geometry(f"{width}x{height}+20+20")
        factor = max(1.0, min(3.0, self._tk_scale / 1.333))
        self.root.minsize(
            min(width, round(350 * factor)),
            min(height, round((410 if self.voice_model_dir else 260) * factor)),
        )
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._visible = False
        self._pending_fetch = False
        self._closed = False
        self._poll_after_id: str | None = None
        self._voice_after_id: str | None = None
        self._preview_after_id: str | None = None
        self._preview_step = 0
        self._narrow_controls: bool | None = None
        self._voice_controls_frame: tk.Frame | None = None
        self._current_session: str | None = None
        self._control_in_flight = False
        self._display_revision = 0
        self._preview_registry = HudRegistry() if preview else None
        self._build()
        if self.voice_model_dir is not None:
            from chaser_agent.desktop_voice import DesktopVoiceController

            self._voice_after_id = self.root.after(100, self._drain_voice_events)
            self._voice_controller = DesktopVoiceController(
                model_dir=self.voice_model_dir, on_event=self._queue_voice_event,
            )
            self._voice_controller.start()
        if preview:
            self._show_preview()
        else:
            if show_idle:
                self._visible = True
                self.phase_label.configure(text="Connecting")
                self.action_label.configure(text=f"Starting the local review service on port {port}.")
                self.notice_label.configure(text="Computer-use controls are inactive until an executor connects.")
            else:
                self.root.withdraw()
            self._poll_after_id = self.root.after(100, self._poll)

    def _build(self) -> None:
        container = tk.Frame(self.root, bg=INK)
        container.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(container, bg=PANEL, highlightthickness=0, borderwidth=0)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        wrapper = tk.Frame(self._canvas, bg=PANEL, padx=20, pady=18)
        self._canvas_window = self._canvas.create_window((0, 0), window=wrapper, anchor="nw")
        wrapper.bind("<Configure>", self._resize_scroll_region)
        self._canvas.bind("<Configure>", self._resize_canvas_content)
        self.root.bind("<MouseWheel>", self._scroll_wheel)
        header = tk.Frame(wrapper, bg=PANEL)
        header.pack(fill="x")
        tk.Label(header, text="CHASER AGENT", bg=PANEL, fg=EDGE,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(header, text="SYNTHETIC PREVIEW" if self.preview else "COMPUTER USE HUD",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(side="right")
        self.phase_label = tk.Label(wrapper, text="Waiting", bg=PANEL, fg=BONE,
                                    font=("Segoe UI", 21, "bold"), anchor="w")
        self.phase_label.pack(fill="x", pady=(16, 3))
        self.action_label = tk.Label(wrapper, text="No computer-use session is connected.",
                                     bg=PANEL, fg=BONE, font=("Segoe UI", 11),
                                     anchor="w", justify="left", wraplength=self._wrap_length)
        self.action_label.pack(fill="x")
        self.session_label = tk.Label(wrapper, text="", bg=PANEL, fg=MUTED,
                                      font=("Segoe UI", 9), anchor="w")
        self.session_label.pack(fill="x", pady=(12, 0))
        separator = tk.Frame(wrapper, height=1, bg="#2B3748")
        separator.pack(fill="x", pady=(14, 12))
        controls = tk.Frame(wrapper, bg=PANEL)
        controls.pack(fill="x")
        self._hud_controls_frame = controls
        for column in range(4):
            controls.grid_columnconfigure(column, weight=1, uniform="hud-control")
        style = ttk.Style(self.root)
        style.configure("Hud.TButton", font=("Segoe UI", 9), padding=(9, 6))
        self.buttons = {}
        for column, (command, label) in enumerate((("pause", "Pause"), ("resume", "Resume"),
                                                  ("stop", "Stop"), ("take_over", "Take over"))):
            button = ttk.Button(controls, text=label, style="Hud.TButton", state="disabled",
                                command=lambda selected=command: self._request_control(selected))
            button.grid(row=0, column=column, sticky="ew", padx=(0, 5) if column < 3 else (0, 0))
            self.buttons[command] = button
        self.notice_label = tk.Label(wrapper, text="Controls wait for a verified executor connection.",
                                      bg=PANEL, fg=MUTED, font=("Segoe UI", 8), anchor="w")
        self.notice_label.pack(fill="x", pady=(10, 0))
        if self.voice_model_dir is not None:
            self._build_voice(wrapper)

    def _build_voice(self, wrapper: tk.Frame) -> None:
        tk.Frame(wrapper, height=1, bg="#2B3748").pack(fill="x", pady=(14, 12))
        tk.Label(wrapper, text="VOICE · PUSH TO TALK", bg=PANEL, fg=EDGE,
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
        self.voice_state_label = tk.Label(
            wrapper, text="Loading the optional offline speech model…", bg=PANEL,
            fg=MUTED, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=self._wrap_length,
        )
        self.voice_state_label.pack(fill="x", pady=(6, 2))
        self.voice_draft_label = tk.Label(
            wrapper, text="No draft. The microphone is off.", bg=PANEL,
            fg=BONE, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=self._wrap_length,
        )
        self.voice_draft_label.pack(fill="x", pady=(0, 7))
        row = tk.Frame(wrapper, bg=PANEL)
        row.pack(fill="x")
        self._voice_controls_frame = row
        for column in range(3):
            row.grid_columnconfigure(column, weight=1, uniform="voice-control")
        self.talk_button = ttk.Button(row, text="Talk", state="disabled", style="Hud.TButton",
                                      command=self._voice_talk)
        self.talk_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.speak_button = ttk.Button(row, text="Speak status", state="disabled", style="Hud.TButton",
                                       command=self._voice_speak)
        self.speak_button.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.clear_button = ttk.Button(row, text="Clear draft", state="disabled", style="Hud.TButton",
                                       command=self._voice_clear)
        self.clear_button.grid(row=0, column=2, sticky="ew")

    def _resize_scroll_region(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        if self._canvas.winfo_height() <= 1:
            return
        overflow = self._canvas.bbox("all")[3] > self._canvas.winfo_height() + 1
        if overflow and not self._scrollbar.winfo_ismapped():
            self._scrollbar.pack(side="right", fill="y")
        elif not overflow and self._scrollbar.winfo_ismapped():
            self._scrollbar.pack_forget()

    def _resize_canvas_content(self, event) -> None:
        self._canvas.itemconfigure(self._canvas_window, width=event.width)
        wrap = max(160, event.width - 40)
        self._wrap_length = wrap
        for label in (self.phase_label, self.action_label, self.session_label, self.notice_label):
            label.configure(wraplength=wrap, justify="left")
        if self.voice_model_dir is not None:
            self.voice_state_label.configure(wraplength=wrap)
            self.voice_draft_label.configure(wraplength=wrap)
        self._layout_controls(event.width < 340)
        self._resize_scroll_region()

    def _layout_controls(self, narrow: bool) -> None:
        if narrow == self._narrow_controls:
            return
        self._narrow_controls = narrow
        frame = self._hud_controls_frame
        for column in range(4):
            frame.grid_columnconfigure(column, weight=1 if not narrow or column < 2 else 0,
                                       uniform="hud-control" if not narrow or column < 2 else "")
        for index, command in enumerate(("pause", "resume", "stop", "take_over")):
            row, column = (divmod(index, 2) if narrow else (0, index))
            self.buttons[command].grid_configure(
                row=row, column=column, padx=(0, 5) if column < (1 if narrow else 3) else 0,
                pady=(0, 5) if narrow and row == 0 else 0,
            )
        voice_frame = self._voice_controls_frame
        if voice_frame is not None:
            for column in range(3):
                voice_frame.grid_columnconfigure(column, weight=1 if not narrow or column < 2 else 0,
                                                  uniform="voice-control" if not narrow or column < 2 else "")
            for index, button in enumerate((self.talk_button, self.speak_button, self.clear_button)):
                row, column, span = (1, 0, 2) if narrow and index == 2 else (0, index, 1)
                button.grid_configure(row=row, column=column, columnspan=span,
                                      padx=(0, 5) if row == 0 and column < (1 if narrow else 2) else 0,
                                      pady=(0, 5) if narrow and row == 0 else 0)

    def _scroll_wheel(self, event) -> None:
        if self._scrollbar.winfo_ismapped():
            self._canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _queue_voice_event(self, event: str, payload: dict[str, object] | None = None) -> None:
        if self._closed:
            return
        if threading.get_ident() == self._ui_thread_id:
            self._on_voice_event(event, payload)
            if event == "recording":
                # Paint the consent indicator before the worker opens a device.
                self.root.update_idletasks()
            return
        self._voice_events.put((event, payload))

    def _drain_voice_events(self) -> None:
        if self._closed:
            return
        while True:
            try:
                event, payload = self._voice_events.get_nowait()
            except queue.Empty:
                break
            if event == "speech_complete" and payload is not None:
                self._finish_speech(str(payload.get("message") or "Status speech unavailable"))
            else:
                self._on_voice_event(event, payload)
        self._voice_after_id = self.root.after(100, self._drain_voice_events)

    def _on_voice_event(self, event: str, payload: dict[str, object] | None) -> None:
        if self._closed:
            return
        capture_id = payload.get("capture_id") if payload is not None else None
        if isinstance(capture_id, int) and not isinstance(capture_id, bool):
            if event == "recording":
                self._active_capture_id = capture_id
            elif capture_id != getattr(self, "_active_capture_id", None):
                # A previous take may finish after a new recording starts.
                return
        if event == "loading":
            self.voice_state_label.configure(text="Loading the optional offline speech model…")
        elif event == "ready":
            self.talk_button.configure(state="normal", text="Talk")
            self.voice_state_label.configure(text="Ready · press Talk for one 5-second take", fg=MUTED)
        elif event == "model_unavailable":
            self.voice_state_label.configure(text="Voice input unavailable · check the local model and optional dependencies")
        elif event == "recording":
            self.talk_button.configure(state="normal", text="Cancel take")
            self.speak_button.configure(state="disabled")
            self.voice_state_label.configure(text="MICROPHONE ACTIVE · press Cancel take to discard", fg=PHASE_COLORS["failed"])
            self.voice_draft_label.configure(text="Recording one take in memory; no transcript yet.")
        elif event == "cancelling":
            self.talk_button.configure(state="disabled")
            self.voice_state_label.configure(text="Cancelling take · microphone closing")
        elif event == "transcribing":
            self.talk_button.configure(state="normal", text="Cancel take")
            self.voice_state_label.configure(text="MICROPHONE OFF · transcribing locally", fg=MUTED)
            self.voice_draft_label.configure(text="Recording ended; preparing an unverified draft.")
        elif event == "draft" and payload is not None:
            text = payload.get("text")
            self._voice_draft = text if isinstance(text, str) and len(text) <= 2000 else None
            display = self._voice_draft or "Invalid draft discarded."
            self.voice_draft_label.configure(text=f"Draft (unverified): {display[:150]}{'…' if len(display) > 150 else ''}")
            self.voice_state_label.configure(text="Microphone off · draft is not a command", fg=MUTED)
            self.talk_button.configure(state="normal", text="Talk")
            self.clear_button.configure(state="normal" if self._voice_draft else "disabled")
            self.speak_button.configure(
                state="normal" if self.voice_output_enabled and status_intent(self._voice_draft or "") else "disabled",
            )
        else:
            self.talk_button.configure(state="normal", text="Talk")
            if self._voice_draft is None:
                self.voice_draft_label.configure(text="No draft. The microphone is off.")
            self.voice_state_label.configure(text={
                "cancelled": "Take discarded · microphone off",
                "no_speech": "No speech detected · microphone off",
                "transcription_unavailable": "Transcription unavailable · microphone off",
            }.get(event, "Microphone off"), fg=MUTED)

    def _voice_talk(self) -> None:
        if self._voice_controller is None or self._closed:
            return
        if self._speech_busy:
            self._barge_in_pending = True
            self._speech_cancel.set()
            self.talk_button.configure(state="disabled", text="Talk queued")
            self.speak_button.configure(state="disabled", text="Stopping reply")
            self.voice_state_label.configure(text="Stopping reply before opening the microphone…")
            return
        if self._voice_controller.is_busy():
            self._voice_controller.cancel()
            return
        self._voice_clear()
        if not self._voice_controller.capture():
            self.voice_state_label.configure(text="Voice input unavailable · microphone off", fg=MUTED)

    def _voice_clear(self) -> None:
        self._barge_in_pending = False
        if self._speech_busy:
            self._speech_cancel.set()
            self.voice_state_label.configure(text="Stopping the local reply…")
        self._voice_draft = None
        self.voice_draft_label.configure(text="No draft. The microphone is off.")
        self.speak_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")

    def _voice_speak(self) -> None:
        if self._closed or not self.voice_output_enabled:
            return
        if self._speech_busy:
            self._speech_cancel.set()
            self.speak_button.configure(state="disabled", text="Stopping…")
            self.voice_state_label.configure(text="Stopping the local reply…")
            return
        if not self._voice_draft or status_intent(self._voice_draft) is None:
            return
        self._speech_cancel = threading.Event()
        self._speech_busy = True
        self._barge_in_pending = False
        self.speak_button.configure(state="normal", text="Cancel reply")
        self.talk_button.configure(state="normal", text="Talk next")
        self.voice_state_label.configure(text="Reply pending · Talk next stops it before recording")
        draft = self._voice_draft
        threading.Thread(target=self._speak_in_background, args=(draft,),
                         name="chaser-local-status-speech", daemon=True).start()

    def _speak_in_background(self, draft: str) -> None:
        from chaser_agent.voice_ack import speak_status_reply

        try:
            spoken = speak_status_reply(
                data_dir=self.token_file.parent, transcript=draft, port=self.port,
                cancel_event=self._speech_cancel,
            )
            message = f"Spoken: {spoken[0]}" if spoken is not None else "No supported status question."
        except (OSError, ValueError, RuntimeError, TimeoutError):
            message = ("Reply stop requested · playback may have already started"
                       if self._speech_cancel.is_set()
                       else "Status speech unavailable · check the local voice service")
        if not self._closed:
            self._voice_events.put(("speech_complete", {"message": message}))

    def _finish_speech(self, message: str) -> None:
        self._speech_busy = False
        barge_in = getattr(self, "_barge_in_pending", False)
        self._barge_in_pending = False
        self.voice_state_label.configure(text=message, fg=MUTED)
        self.speak_button.configure(text="Speak status", state="disabled")
        if self._voice_controller is not None and not self._voice_controller.is_busy():
            self.talk_button.configure(state="normal", text="Talk")
        if self._voice_draft and status_intent(self._voice_draft):
            self.speak_button.configure(state="normal")
        if barge_in and not self._closed:
            self._voice_talk()

    def _render(self, state: dict[str, object]) -> None:
        self._display_revision = getattr(self, "_display_revision", 0) + 1
        phase = state.get("phase")
        if state.get("status") == "inactive" and not self.preview:
            self._current_session = None
            for button in self.buttons.values():
                button.configure(state="disabled")
            if self.show_idle:
                if not self._visible:
                    self.root.deiconify()
                    self._visible = True
                self.phase_label.configure(text="Local service ready", fg=PHASE_COLORS["running"])
                self.action_label.configure(text="No computer-use session is connected.")
                self.session_label.configure(text=f"Local API 127.0.0.1:{self.port}")
                self.notice_label.configure(text="Review-only · controls require an authorized executor")
            elif self._visible:
                self.root.withdraw()
                self._visible = False
            return
        self._current_session = str(state.get("session_id")) if state.get("session_id") else None
        available = set(state.get("available_controls") or []) if not self.preview and not self._control_in_flight else set()
        for command, button in self.buttons.items():
            button.configure(state="normal" if command in available else "disabled")
        if not self._visible:
            self.root.deiconify()
            self._visible = True
        disconnected = state.get("connected") is False and phase not in {None, "completed", "failed", "stopped"}
        label = "Connection lost" if disconnected else str(phase or "Awaiting session").replace("_", " ").title()
        color = PHASE_COLORS["failed"] if disconnected else PHASE_COLORS.get(str(phase), BONE)
        self.phase_label.configure(text=label, fg=color)
        action = str(state.get("action") or "Waiting for the next verified status event.")
        self.action_label.configure(text=f"Last reported {phase}: {action}" if disconnected else action)
        self.session_label.configure(text=f"Session {state.get('session_id') or '—'}  ·  Event {state.get('sequence', '—')}")
        notice = "Execution status unknown · no controls available" if disconnected else state.get("notice")
        self.notice_label.configure(text=str(notice or "Display only · controls require an executor"))

    def _request_control(self, command: str) -> None:
        if self.preview or self._closed or self._control_in_flight or not self._current_session:
            return
        self._control_in_flight = True
        self.notice_label.configure(text="Sending control request · waiting for executor evidence")
        for button in self.buttons.values():
            button.configure(state="disabled")
        session_id = self._current_session
        revision = self._display_revision
        threading.Thread(target=self._control_in_background, args=(session_id, command, revision), daemon=True).start()

    def _control_in_background(self, session_id: str, command: str, revision: int) -> None:
        try:
            result = send_control(port=self.port, token=self.token, session_id=session_id, command=command)
            notice = ("Awaiting executor acknowledgement" if result.get("status") == "pending_executor_ack"
                      else "Executor acknowledgement received" if result.get("status") == "acknowledged"
                      else "Control status unknown")
        except (OSError, URLError, HTTPError, ValueError, json.JSONDecodeError):
            notice = "Control request failed · execution status unknown"
        if not self._closed:
            try:
                self.root.after(0, lambda: self._finish_control(notice, session_id, revision))
            except (RuntimeError, tk.TclError):
                pass

    def _finish_control(self, notice: str, session_id: str, revision: int) -> None:
        self._control_in_flight = False
        if self._current_session == session_id and self._display_revision == revision:
            self.notice_label.configure(text=notice)

    def _poll(self) -> None:
        if self._closed:
            return
        if not self._pending_fetch:
            self._pending_fetch = True
            threading.Thread(target=self._fetch_in_background, daemon=True).start()
        self._poll_after_id = self.root.after(600, self._poll)

    def _fetch_in_background(self) -> None:
        try:
            snapshot = fetch_snapshot(port=self.port, token=self.token)
        except (OSError, URLError, ValueError, json.JSONDecodeError):
            snapshot = None
        if not self._closed:
            try:
                self.root.after(0, lambda: self._finish_fetch(snapshot))
            except (RuntimeError, tk.TclError):
                pass

    def _finish_fetch(self, snapshot: dict[str, object] | None) -> None:
        self._pending_fetch = False
        if snapshot is None:
            self._display_revision = getattr(self, "_display_revision", 0) + 1
            self._current_session = None
            for button in self.buttons.values():
                button.configure(state="disabled")
            if self._visible:
                self.phase_label.configure(text="Connection lost", fg=PHASE_COLORS["failed"])
                self.notice_label.configure(text="Execution status unknown · no controls available")
            return
        self._render(snapshot)

    def _show_preview(self) -> None:
        registry = self._preview_registry
        if self._preview_step == 0:
            registry.begin_session("synthetic-preview")
            registry.receive_event(session_id="synthetic-preview", sequence=0, phase="running",
                                   action="Reviewing a safe example task. No computer control is active.")
        elif self._preview_step == 1:
            registry.receive_event(session_id="synthetic-preview", sequence=1, phase="awaiting_approval",
                                   action="A proposed action would wait for your approval.")
        elif self._preview_step == 2:
            registry.receive_event(session_id="synthetic-preview", sequence=2, phase="paused",
                                   action="Synthetic session paused; no executor is connected.")
        elif self._preview_step == 3:
            registry.receive_event(session_id="synthetic-preview", sequence=3, phase="stopped",
                                   action="Synthetic replay stopped. Terminal state stays visible.")
        self._render(registry.snapshot())
        self._preview_step += 1
        if self._preview_step < 4:
            self._preview_after_id = self.root.after(2500, self._show_preview)

    def run(self) -> None:
        self.root.mainloop()

    def _on_close(self) -> None:
        self.close()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._speech_cancel.set()
            self._barge_in_pending = False
            if self._voice_controller is not None:
                self._voice_controller.close()
            self._voice_draft = None
            for after_id in (self._poll_after_id, self._voice_after_id, self._preview_after_id):
                if after_id is not None:
                    try:
                        self.root.after_cancel(after_id)
                    except tk.TclError:
                        pass
            self.root.destroy()
