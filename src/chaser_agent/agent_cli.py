"""Talk to the running service from a terminal or another harness.

These commands read the private token themselves, so a caller never handles it and
it never appears in a command line or transcript.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from chaser_agent.agent.events import with_io_retry
from chaser_agent.local_acl import read_private_control_token

DEFAULT_DATA_DIR_ENV = "CHASER_AGENT_DATA_DIR"
TERMINAL = {"finished", "failed", "cancelled", "budget_stopped", "interrupted", "awaiting_human", "awaiting_approval"}
_TOKENS: dict[str, str] = {}


def _data_dir(args: argparse.Namespace) -> Path:
    value = args.data_dir or os.environ.get(DEFAULT_DATA_DIR_ENV)
    if not value:
        raise ValueError(f"Pass --data-dir or set {DEFAULT_DATA_DIR_ENV}")
    return Path(value)


def _token(args: argparse.Namespace) -> str:
    """Check the private folder once per process: each check starts PowerShell twice."""
    folder = str(_data_dir(args))
    if folder not in _TOKENS:
        _TOKENS[folder] = with_io_retry(lambda: read_private_control_token(Path(folder)))
    return _TOKENS[folder]


def _call(args: argparse.Namespace, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    token = _token(args)
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(f"http://127.0.0.1:{args.port}{path}", data=data, method=method, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return 503, {"error": {"code": "service_unreachable", "message": f"Nothing answered on port {args.port}"}}


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", help=f"Private runtime directory (or {DEFAULT_DATA_DIR_ENV}).")
    parser.add_argument("--port", type=int, default=8765)


def _describe(event: dict[str, Any]) -> str | None:
    data = event["data"]
    kind = event["type"]
    if kind == "reasoner_reply":
        return f"[thinking] {data.get('thought')}"
    if kind == "tool_started":
        return f"[tool] {data.get('tool')}"
    if kind == "tool_denied":
        return f"[denied] {data.get('tool')}: {data.get('reason')}"
    if kind == "question_asked":
        return f"[question {data.get('question_id')}] {data.get('question')}"
    if kind == "approval_requested":
        return f"[approval {data.get('approval_id')}] {data.get('tool')} {json.dumps(data.get('args'), ensure_ascii=False)[:400]}"
    if kind == "turn_finished":
        return f"[{data.get('status')}] {data.get('answer') or data.get('error') or ''}"
    return None


def run_ask(args: argparse.Namespace) -> int:
    message = " ".join(args.message)
    if args.session:
        status, session = _call(args, "POST", f"/v1/agent/sessions/{args.session}/messages", {"message": message})
    else:
        body: dict[str, Any] = {"message": message, "reasoner": args.reasoner}
        if args.workflow:
            body["workflow"] = args.workflow
        if args.withhold:
            body["withhold_tools"] = args.withhold
        status, session = _call(args, "POST", "/v1/agent/sessions", body)
    if status not in {201, 202}:
        print(f"error: {session}", file=sys.stderr)
        return 2
    print(f"session {session['id']} · workflow {session['workflow']}", flush=True)
    seen = session["events"] - 1 if args.session else 0
    while True:
        _, page = _call(args, "GET", f"/v1/agent/sessions/{session['id']}/events?after={seen}")
        for event in page.get("events", []):
            seen = event["seq"]
            line = _describe(event)
            if line:
                print(line, flush=True)
        _, snapshot = _call(args, "GET", f"/v1/agent/sessions/{session['id']}")
        if snapshot["status"] in TERMINAL and not page.get("events"):
            return 0 if snapshot["status"] == "finished" else 1
        time.sleep(1.5)


def _new_since(previous: str, current: str) -> str:
    """What was added to the conversation, for a harness that remembers the earlier part."""
    shared = len(os.path.commonprefix([previous, current]))
    return current[current.rfind("\n\n", 0, shared) + 2 if shared else 0 :]


def run_reasoner_next(args: argparse.Namespace) -> int:
    deadline = time.monotonic() + args.wait
    while True:
        status, value = _call(args, "GET", "/v1/agent/reasoner/next")
        if status not in {200, 503}:
            print(json.dumps(value), file=sys.stderr)
            return 2
        request = value.get("request")
        if request and not args.out_dir:
            print(f"REQUEST_ID: {request['request_id']}\n\n===== SYSTEM =====\n{request['system']}\n\n===== CONVERSATION =====\n{request['transcript']}")
            return 0
        if request:
            folder = Path(args.out_dir)
            folder.mkdir(parents=True, exist_ok=True)
            conversation = folder / "conversation.txt"
            previous = conversation.read_text(encoding="utf-8") if conversation.is_file() else ""
            (folder / "system.txt").write_text(request["system"], encoding="utf-8")
            conversation.write_text(request["transcript"], encoding="utf-8")
            (folder / "new.txt").write_text(_new_since(previous, request["transcript"]), encoding="utf-8")
            print(f"REQUEST_ID: {request['request_id']}\nSystem: {folder / 'system.txt'}\nFull conversation: {conversation}\nNew since your last reply: {folder / 'new.txt'}")
            return 0
        if time.monotonic() >= deadline:
            print("NO_REQUEST_WAITING")
            return 3
        time.sleep(1.0)


def run_reasoner_reply(args: argparse.Namespace) -> int:
    text = Path(args.file).read_text(encoding="utf-8")
    status, value = _call(args, "POST", "/v1/agent/reasoner/reply", {"request_id": args.request_id, "text": text, "model": args.model})
    print(json.dumps(value))
    return 0 if status == 202 else 2


def run_status(args: argparse.Namespace) -> int:
    status, value = _call(args, "GET", "/v1/agent/status")
    print(json.dumps(value if not args.brief else {
        "tools": [tool["tool"] for tool in value.get("tools", [])],
        "workflows": value.get("workflows"), "reasoners": value.get("reasoners"),
        "active_sessions": value.get("active_sessions"), "waiting_for_operator": value.get("waiting_for_operator"),
    }, ensure_ascii=False, indent=1))
    return 0 if status == 200 else 2


def is_hud_title(title: str) -> bool:
    """The HUD's window title: "Chaser", or "Needs your yes · Chaser" while it waits. Older pages said "Chaser Agent"."""
    return title in {"Chaser", "Chaser Agent"} or title.endswith((" · Chaser", " · Chaser Agent"))


class _HudWindow:
    """The HUD's window on Windows: found by title, kept above other windows, in the bottom-right corner."""

    MARGIN = 16

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        self.ctypes, self.wintypes = ctypes, wintypes
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows.argtypes = [self.callback, wintypes.LPARAM]
        self.user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        for name in ("IsWindowVisible", "IsIconic"):
            getattr(self.user32, name).argtypes = [wintypes.HWND]
        self.user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]

    def find(self) -> int | None:
        found: list[int] = []

        def visit(window: int, _extra: int) -> bool:
            text = self.ctypes.create_unicode_buffer(64)
            if self.user32.IsWindowVisible(window) and self.user32.GetWindowTextW(window, text, 64) and is_hud_title(text.value):
                found.append(window)
            return True

        self.user32.EnumWindows(self.callback(visit), 0)
        return found[0] if found else None

    def place(self, window: int, width: int | None = None, height: int | None = None) -> None:
        area, now = self.wintypes.RECT(), self.wintypes.RECT()
        self.user32.SystemParametersInfoW(0x0030, 0, self.ctypes.byref(area), 0)  # SPI_GETWORKAREA
        self.user32.GetWindowRect(window, self.ctypes.byref(now))
        width, height = width or now.right - now.left, height or now.bottom - now.top
        topmost, no_activate = self.wintypes.HWND(-1), 0x0010
        self.user32.SetWindowPos(window, topmost, area.right - width - self.MARGIN, area.bottom - height - self.MARGIN, width, height, no_activate)

    def bring_back(self) -> bool:
        """An open HUD comes back rather than a second one starting, even if it was minimized."""
        window = self.find()
        if window is None:
            return False
        if self.user32.IsIconic(window):
            self.user32.ShowWindow(window, 4)  # SW_SHOWNOACTIVATE
            time.sleep(0.5)
        self.place(window)
        return True

    def pin(self, width: int = 436, height: int = 115, wait: float = 30.0) -> bool:
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            window = self.find()
            if window is not None:
                self.place(window, width, height)
                # Edge can still put the window back where it last was as the page finishes loading,
                # so place it once more at whatever size the page has settled on.
                time.sleep(1.5)
                self.place(window)
                return True
            time.sleep(0.2)
        return False


def run_open(args: argparse.Namespace) -> int:
    """Open the HUD with the token in the fragment. Never printed; never sent to a server."""
    token = read_private_control_token(_data_dir(args))
    url = f"http://127.0.0.1:{args.port}/#token={token}"
    pinned = False
    if os.name == "nt":
        hud = _HudWindow()
        if hud.bring_back():
            print(f"The Chaser HUD is already open on port {args.port}, and is back in its corner.")
            return 0
        browser = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
        command = [str(browser), f"--app={url}", "--window-size=436,115"] if browser.is_file() else ["cmd", "/c", "start", "", url]
        subprocess.Popen(command, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        pinned = browser.is_file() and hud.pin()
    else:
        import webbrowser

        webbrowser.open(url)
    print(f"The Chaser HUD opened on port {args.port}{'' if pinned else '. It could not be kept on top'}.")
    return 0


def add_agent_commands(subparsers: argparse._SubParsersAction) -> None:
    ask = subparsers.add_parser("ask", help="Give the running agent a task in one sentence and follow it.")
    _common(ask)
    ask.add_argument("message", nargs="+")
    ask.add_argument("--workflow")
    ask.add_argument("--reasoner", default="auto")
    ask.add_argument("--session", help="Continue this session instead of starting a new one.")
    ask.add_argument("--withhold", action="append", default=[], help="A tool this session must not have, even if its workflow grants it. Repeatable.")
    ask.set_defaults(func=run_ask)

    status = subparsers.add_parser("agent-status", help="Show tools, workflows and which reasoning routes are available.")
    _common(status)
    status.add_argument("--brief", action="store_true")
    status.set_defaults(func=run_status)

    console = subparsers.add_parser("open", help="Open the small always-on-top HUD for the running service.")
    _common(console)
    console.set_defaults(func=run_open)

    reasoner = subparsers.add_parser("reasoner", help="Act as the reasoner for sessions using the bridge route.")
    actions = reasoner.add_subparsers(dest="reasoner_action", required=True)
    next_request = actions.add_parser("next", help="Wait for the next model request and print it.")
    _common(next_request)
    next_request.add_argument("--wait", type=float, default=60.0)
    next_request.add_argument("--out-dir", help="Write the request to files here instead of printing it.")
    next_request.set_defaults(func=run_reasoner_next)
    reply = actions.add_parser("reply", help="Answer a model request with the contents of a file.")
    _common(reply)
    reply.add_argument("request_id")
    reply.add_argument("--file", required=True)
    reply.add_argument("--model", default="external")
    reply.set_defaults(func=run_reasoner_reply)


def run_decide(args: argparse.Namespace) -> int:
    """Approve or reject the session's pending request. Shows exactly what is being decided."""
    status, snapshot = _call(args, "GET", f"/v1/agent/sessions/{args.session_id}")
    pending = snapshot.get("pending") if status == 200 else None
    if not pending or pending.get("kind") != "approval":
        print("Nothing is waiting for approval in that session.")
        return 3
    print(json.dumps({"tool": pending["tool"], "args": pending["args"], "digest": pending["digest"]}, ensure_ascii=False, indent=1))
    if args.decision is None:
        return 0
    status, value = _call(args, "POST", f"/v1/agent/sessions/{args.session_id}/approvals", {
        "approval_id": pending["id"], "digest": pending["digest"], "decision": args.decision, "decided_by": args.decided_by,
    })
    print(f"{args.decision}: {value.get('status') if status == 202 else value}")
    return 0 if status == 202 else 2


def add_decide_command(subparsers: argparse._SubParsersAction) -> None:
    decide = subparsers.add_parser("decide", help="See and answer a session's pending approval.")
    _common(decide)
    decide.add_argument("session_id")
    decide.add_argument("decision", nargs="?", choices=("approve", "reject"), help="Leave out to only look at it.")
    decide.add_argument("--decided-by", default="local_operator")
    decide.set_defaults(func=run_decide)
