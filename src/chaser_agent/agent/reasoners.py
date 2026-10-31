"""Where reasoning comes from. Each reasoner only returns text; none holds authority.

Existing installed routes are reused, each under its own identity, so Chaser Agent
copies no credentials and adds no paid fallback. A route that is down says so and
the turn stops. It never silently switches to a different provider.

The bridge route lets any other harness act as the reasoner over the local API.
It sees only what this loop assembled and its replies pass the same parser, so it
is a useful way to test the loop and to drive it from another agent.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any, Protocol

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# A nested CLI must not inherit a parent harness's session plumbing.
_HARNESS_PREFIXES = ("CLAUDE_", "ANTHROPIC_")
_HARNESS_NAMES = {"CLAUDECODE"}


class ReasonerUnavailable(RuntimeError):
    """The route cannot answer right now. The turn stops and says so."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ReasonerReply:
    text: str
    route: str
    model: str
    seconds: float


class Reasoner(Protocol):
    reasoner_id: str
    label: str

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply: ...

    def status(self) -> dict[str, Any]: ...


def _run_cancellable(command: list[str], *, stdin: str, timeout: float, cancel: Event, env: dict[str, str] | None = None, cwd: str | None = None) -> tuple[int, str]:
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        encoding="utf-8", errors="replace", env=env, cwd=cwd, creationflags=NO_WINDOW,
    )
    result: dict[str, str] = {}

    def communicate() -> None:
        result["stdout"], _ = process.communicate(stdin)

    worker = threading.Thread(target=communicate, daemon=True)
    worker.start()
    deadline = time.monotonic() + timeout
    while worker.is_alive():
        worker.join(0.25)
        if cancel.is_set() or time.monotonic() > deadline:
            process.kill()
            worker.join(5)
            if cancel.is_set():
                raise ReasonerUnavailable("cancelled", "the operator cancelled this turn")
            raise ReasonerUnavailable("timeout", f"no reply within {int(timeout)} seconds")
    return process.returncode, result.get("stdout", "")


class ClaudeCliReasoner:
    """Claude Code's own CLI with every native tool off: it thinks, this loop acts."""

    reasoner_id = "claude-cli"
    label = "Claude (Claude Code login)"

    def __init__(self, model: str = "sonnet", executable: str | None = None) -> None:
        self.model = model
        self.executable = executable or shutil.which("claude")

    @staticmethod
    def _environment() -> dict[str, str]:
        return {
            key: value for key, value in os.environ.items()
            if key not in _HARNESS_NAMES and not key.startswith(_HARNESS_PREFIXES)
        }

    def status(self) -> dict[str, Any]:
        if not self.executable:
            return {"id": self.reasoner_id, "label": self.label, "available": False, "reason": "claude CLI is not installed"}
        try:
            done = subprocess.run(
                [self.executable, "auth", "status"], capture_output=True, encoding="utf-8", errors="replace",
                timeout=20, env=self._environment(), creationflags=NO_WINDOW,
            )
            logged_in = bool(json.loads(done.stdout).get("loggedIn"))
        except (OSError, ValueError, subprocess.SubprocessError):
            logged_in = False
        return {
            "id": self.reasoner_id, "label": self.label, "available": logged_in, "model": self.model,
            "reason": None if logged_in else "This machine's claude CLI is not logged in. Run: claude auth login",
        }

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        if not self.executable:
            raise ReasonerUnavailable("not_installed", "claude CLI is not installed")
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="chaser-reasoner-") as folder:
            prompt_file = Path(folder) / "system.txt"
            prompt_file.write_text(system, encoding="utf-8")
            code, stdout = _run_cancellable(
                [
                    self.executable, "-p", "--output-format", "json", "--tools", "", "--no-session-persistence",
                    "--strict-mcp-config", "--setting-sources", "", "--model", self.model,
                    "--system-prompt-file", str(prompt_file),
                ],
                stdin=transcript, timeout=timeout, cancel=cancel, env=self._environment(), cwd=folder,
            )
        try:
            value = json.loads(stdout)
        except ValueError as exc:
            raise ReasonerUnavailable("bad_output", f"claude CLI exit {code} returned no JSON") from exc
        text = value.get("result")
        if value.get("is_error") or not isinstance(text, str) or not text.strip():
            detail = str(text or value.get("terminal_reason") or "error")[:300]
            raise ReasonerUnavailable("route_error", detail)
        return ReasonerReply(text, self.reasoner_id, self.model, round(time.monotonic() - started, 3))


class HermesTextReasoner:
    """The existing zero-tool Hermes route on its own subscription. No fallback is added."""

    reasoner_id = "hermes-text"
    label = "Hermes (OpenAI subscription)"

    def __init__(self, python_executable: str, script: Path, model: str = "gpt-5.6-sol") -> None:
        self.python_executable = python_executable
        self.script = script
        self.model = model
        self._status: dict[str, Any] | None = None
        self._status_at = 0.0

    def _call(self, request: dict[str, Any], *, timeout: float, cancel: Event) -> dict[str, Any]:
        code, stdout = _run_cancellable(
            [self.python_executable, "-I", "-B", "-X", "utf8", str(self.script)],
            stdin=json.dumps(request, ensure_ascii=False), timeout=timeout, cancel=cancel,
        )
        try:
            value = json.loads(stdout)
        except ValueError as exc:
            raise ReasonerUnavailable("bad_output", f"Hermes text route exit {code} returned no JSON") from exc
        if not value.get("ok"):
            kind = value.get("error_type") or value.get("error")
            hint = " This usually means its subscription's usage limit was reached." if kind == "AuthError" else ""
            raise ReasonerUnavailable("route_error", f"Hermes could not answer ({kind}).{hint}")
        return value

    def status(self) -> dict[str, Any]:
        if self._status is not None and time.monotonic() - self._status_at < 300:
            return self._status
        state: dict[str, Any] = {"id": self.reasoner_id, "label": self.label, "model": self.model}
        try:
            self._call({"message": "", "inspect_only": True}, timeout=60, cancel=Event())
            state.update(available=True, reason=None)
        except ReasonerUnavailable as exc:
            state.update(available=False, reason=exc.message)
        except OSError as exc:
            state.update(available=False, reason=f"The Hermes route could not start: {type(exc).__name__}")
        self._status, self._status_at = state, time.monotonic()
        return state

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        started = time.monotonic()
        value = self._call({"message": system + "\n\n" + transcript}, timeout=timeout, cancel=cancel)
        return ReasonerReply(str(value.get("text") or ""), self.reasoner_id, str(value.get("model") or self.model), round(time.monotonic() - started, 3))


class BridgeReasoner:
    """Another harness answers over the local API. One waiter per request."""

    reasoner_id = "bridge"
    label = "Another harness over the local API"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}

    def status(self) -> dict[str, Any]:
        with self._lock:
            waiting = len(self._pending)
        return {"id": self.reasoner_id, "label": self.label, "available": True, "waiting_requests": waiting, "reason": None}

    def next_request(self) -> dict[str, Any] | None:
        with self._lock:
            for request_id, row in self._pending.items():
                if not row["delivered"]:
                    row["delivered"] = True
                    return {"request_id": request_id, "system": row["system"], "transcript": row["transcript"]}
            return None

    def reply(self, request_id: str, text: str, model: str = "external") -> bool:
        with self._lock:
            row = self._pending.get(request_id)
            if row is None:
                return False
            row["text"], row["model"] = text, model
            row["ready"].set()
            return True

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        started = time.monotonic()
        request_id = uuid.uuid4().hex
        ready = Event()
        with self._lock:
            self._pending[request_id] = {"system": system, "transcript": transcript, "ready": ready, "delivered": False}
        try:
            deadline = started + timeout
            while not ready.wait(0.25):
                if cancel.is_set():
                    raise ReasonerUnavailable("cancelled", "the operator cancelled this turn")
                if time.monotonic() > deadline:
                    raise ReasonerUnavailable("timeout", f"no harness replied within {int(timeout)} seconds")
            with self._lock:
                row = self._pending[request_id]
            return ReasonerReply(row["text"], self.reasoner_id, row["model"], round(time.monotonic() - started, 3))
        finally:
            with self._lock:
                self._pending.pop(request_id, None)


class ScriptedReasoner:
    """Replays fixed replies for tests. Never used for a claim about model quality."""

    reasoner_id = "scripted"
    label = "Scripted test replies"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.requests: list[dict[str, str]] = []

    def status(self) -> dict[str, Any]:
        return {"id": self.reasoner_id, "label": self.label, "available": True, "reason": None}

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        self.requests.append({"system": system, "transcript": transcript})
        if not self.replies:
            raise ReasonerUnavailable("exhausted", "no scripted reply left")
        return ReasonerReply(self.replies.pop(0), self.reasoner_id, "scripted", 0.0)
