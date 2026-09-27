"""Small Windows desktop HUD shell driven by authenticated local state.

Controls are only enabled for an attached executor session. A click requests
control; the displayed phase changes only on an executor acknowledgement.
Preview mode is synthetic and never sends a command.
"""

from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from chaser_agent.hud_runtime import HudRegistry

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
    def __init__(self, *, port: int = 8765, token_file: Path | None = None, preview: bool = False):
        if not preview and token_file is None:
            raise ValueError("A local token file is required outside preview mode")
        self.port = port
        self.token_file = token_file
        self.preview = preview
        self.root = tk.Tk()
        self.root.title("Chaser Agent HUD")
        self.root.configure(bg=INK)
        self.root.geometry("410x284+60+80")
        self.root.minsize(350, 260)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._visible = False
        self._pending_fetch = False
        self._closed = False
        self._preview_step = 0
        self._current_session: str | None = None
        self._control_in_flight = False
        self._preview_registry = HudRegistry() if preview else None
        self._build()
        if preview:
            self._show_preview()
        else:
            self.root.withdraw()
            self.root.after(100, self._poll)

    def _build(self) -> None:
        wrapper = tk.Frame(self.root, bg=PANEL, padx=20, pady=18)
        wrapper.pack(fill="both", expand=True, padx=2, pady=2)
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
                                     anchor="w", justify="left", wraplength=350)
        self.action_label.pack(fill="x")
        self.session_label = tk.Label(wrapper, text="", bg=PANEL, fg=MUTED,
                                      font=("Segoe UI", 9), anchor="w")
        self.session_label.pack(fill="x", pady=(12, 0))
        separator = tk.Frame(wrapper, height=1, bg="#2B3748")
        separator.pack(fill="x", pady=(14, 12))
        controls = tk.Frame(wrapper, bg=PANEL)
        controls.pack(fill="x")
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

    def _render(self, state: dict[str, object]) -> None:
        phase = state.get("phase")
        if state.get("status") == "inactive" and not self.preview:
            self._current_session = None
            for button in self.buttons.values():
                button.configure(state="disabled")
            if self._visible:
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
        for button in self.buttons.values():
            button.configure(state="disabled")
        session_id = self._current_session
        threading.Thread(target=self._control_in_background, args=(session_id, command), daemon=True).start()

    def _control_in_background(self, session_id: str, command: str) -> None:
        try:
            token = self.token_file.read_text(encoding="ascii").strip()
            result = send_control(port=self.port, token=token, session_id=session_id, command=command)
            notice = ("Awaiting executor acknowledgement" if result.get("status") == "pending_executor_ack"
                      else "Executor acknowledgement received" if result.get("status") == "acknowledged"
                      else "Control status unknown")
        except (OSError, URLError, HTTPError, ValueError, json.JSONDecodeError):
            notice = "Control request failed · execution status unknown"
        if not self._closed:
            try:
                self.root.after(0, lambda: self._finish_control(notice))
            except (RuntimeError, tk.TclError):
                pass

    def _finish_control(self, notice: str) -> None:
        self._control_in_flight = False
        self.notice_label.configure(text=notice)

    def _poll(self) -> None:
        if self._closed:
            return
        if not self._pending_fetch:
            self._pending_fetch = True
            threading.Thread(target=self._fetch_in_background, daemon=True).start()
        self.root.after(600, self._poll)

    def _fetch_in_background(self) -> None:
        try:
            token = self.token_file.read_text(encoding="ascii").strip()
            snapshot = fetch_snapshot(port=self.port, token=token)
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
            self.root.after(2500, self._show_preview)

    def run(self) -> None:
        self.root.mainloop()

    def _on_close(self) -> None:
        self._closed = True
        self.root.destroy()
