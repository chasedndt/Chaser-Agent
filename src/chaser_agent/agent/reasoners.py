"""Where reasoning comes from. Each reasoner only returns text; none holds authority.

Existing installed routes are reused, each under its own identity, so Chaser Agent
copies no credentials and adds no paid fallback. ChaseOS Cloud is a chosen route on
the owner's own key, not a fallback. A route that is down says so and the turn stops.
It never silently switches to a different provider.

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
BRIDGE_LEASE_SECONDS = 240.0
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
    # What the route says it charged, for the receipt. None where a route charges nothing or does not say.
    credits: int | None = None
    # Tokens, pricing profile and the model that actually served it, where the route reports them. Metadata only.
    usage: dict[str, Any] | None = None


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


CLOUD_KEY_ENV = "CHASEOS_CLOUD_KEY"
CLOUD_BASE_URL = "https://chaseos.ai/api/cloud"
# Cloudflare in front of the gateway refuses Python's default user agent with a 403 that looks like a bad key.
CLOUD_USER_AGENT = "ChaserAgent/1 (+https://chaseos.ai)"
# Names this caller so the gateway can price and report it as an agent harness, not a chat window.
CLOUD_HARNESS = "chaser"
CLOUD_RETRY_STATUSES = frozenset({502, 503, 504})


class ChaseOSCloudReasoner:
    """ChaseOS Cloud: the route meant for unattended work, metered in credits on the owner's own key.

    The key is taken out of the environment when the service starts, so tools and other
    harnesses this service launches never inherit it. A 402 means out of credits: the turn
    stops and says so, never switching to another provider.
    """

    reasoner_id = "chaseos-cloud"
    label = "ChaseOS Cloud"
    max_context_chars = 120_000
    sees_images = True  # OpenAI-style image parts; whether the model reads them depends on the model

    def __init__(self, key: str = "", *, model: str = "chaseos/balanced", base_url: str = "", max_tokens: int = 8000, key_source: str = "") -> None:
        self._key = key.strip()
        self.key_source = (key_source or "given") if self._key else "none"
        self.refused: str | None = None
        self.model = model
        self.base_url = (base_url or CLOUD_BASE_URL).rstrip("/")
        self.max_tokens = max_tokens

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None, *, saved: bool | None = None, **kwargs: Any) -> "ChaseOSCloudReasoner":
        """The key from the environment (a vault injecting it), else the one saved for this Windows account.

        The saved key is read only for the real environment, unless saved=True is passed.
        """
        if saved is None:
            saved = environ is None
        environ = os.environ if environ is None else environ
        key = environ.pop(CLOUD_KEY_ENV, "")
        source = "environment" if key.strip() else ""
        if not source and saved:
            from chaser_agent import cloud_key

            key = cloud_key.load()
            source = "saved" if key else ""
        base_url = kwargs.pop("base_url", "") or environ.get("CHASEOS_CLOUD_BASE_URL", "")
        # A different model, e.g. a candidate evaluated against an OpenAI-compatible endpoint.
        model = kwargs.pop("model", "") or environ.get("CHASEOS_CLOUD_MODEL", "") or "chaseos/balanced"
        return cls(key, base_url=base_url, model=model, key_source=source, **kwargs)

    def set_key(self, key: str, *, source: str = "saved") -> None:
        """Use a key added or removed in Settings from the next step on. Nothing restarts."""
        self._key = (key or "").strip()
        self.key_source = source if self._key else "none"
        self.refused = None

    REFUSAL_MEMORY_SECONDS = 600.0

    def _refuse(self, code: str, message: str) -> ReasonerUnavailable:
        """Remember why the key was refused, so status says so instead of 'ready' for a while. A later success,
        a new key or ten minutes clears it, so topping up the plan doesn't leave the route stuck."""
        self.refused, self.refused_at = message, time.monotonic()
        return ReasonerUnavailable(code, message)

    def _refusal(self) -> str | None:
        if getattr(self, "refused", None) and time.monotonic() - getattr(self, "refused_at", 0.0) < self.REFUSAL_MEMORY_SECONDS:
            return self.refused
        return None

    def status(self) -> dict[str, Any]:
        if self._key and self._refusal():
            return {"id": self.reasoner_id, "label": self.label, "available": False, "model": self.model, "reason": self._refusal()}
        return self._base_status()

    def _base_status(self) -> dict[str, Any]:
        return {
            "id": self.reasoner_id, "label": self.label, "available": bool(self._key), "model": self.model,
            "reason": None if self._key else "No ChaseOS Cloud key yet. Add one in Settings, or run: chaser key add",
        }

    def _endpoint(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json", "User-Agent": CLOUD_USER_AGENT,
                "X-ChaseOS-Agent-Harness": CLOUD_HARNESS}

    def _post(self, body: bytes, timeout: float) -> tuple[int, dict[str, Any]]:
        import urllib.error
        import urllib.request

        request = urllib.request.Request(self._endpoint(), data=body, method="POST", headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - the owner's gateway
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                value = json.loads(exc.read().decode("utf-8", errors="replace") or "{}")
            except ValueError:
                value = {}
            return exc.code, value if isinstance(value, dict) else {}
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            return 0, {}

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event, images: list[Path] | None = None) -> ReasonerReply:
        if not self._base_status().get("available"):  # a remembered refusal still lets an explicit try through
            raise ReasonerUnavailable("not_configured", self._base_status()["reason"])
        started = time.monotonic()
        content: Any = transcript
        if images:
            import base64
            import mimetypes

            content = [{"type": "text", "text": transcript}] + [
                {"type": "image_url", "image_url": {"url": f"data:{mimetypes.guess_type(p.name)[0] or 'image/png'};base64,"
                                                           f"{base64.b64encode(p.read_bytes()).decode('ascii')}"}} for p in images]
        request = {
            "model": self.model, "stream": False, "max_completion_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            # Every reply must be one JSON object; without JSON mode the open models broke the format on about a third of steps.
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(request, ensure_ascii=False).encode("utf-8")
        result: dict[str, Any] = {}

        def call() -> None:
            deadline = started + timeout
            result["reply"] = self._post(body, max(1.0, deadline - time.monotonic()))
            # The gateway sometimes answers 502 and is fine a moment later, so one more try; never more.
            if result["reply"][0] in CLOUD_RETRY_STATUSES | {0} and not cancel.is_set() and deadline - time.monotonic() > 5:
                time.sleep(1)
                result["reply"] = self._post(body, max(1.0, deadline - time.monotonic()))
            # Some providers or models refuse JSON mode outright; ask once more without it. The reply parser still checks the format.
            if result["reply"][0] == 400 and not cancel.is_set() and deadline - time.monotonic() > 5:
                plain = {k: v for k, v in request.items() if k != "response_format"}
                result["reply"] = self._post(json.dumps(plain, ensure_ascii=False).encode("utf-8"), max(1.0, deadline - time.monotonic()))

        worker = threading.Thread(target=call, daemon=True)
        worker.start()
        while worker.is_alive():
            worker.join(0.25)
            if cancel.is_set():
                raise ReasonerUnavailable("cancelled", "the operator cancelled this turn")
            if time.monotonic() - started > timeout + 5:
                raise ReasonerUnavailable("timeout", f"no reply within {int(timeout)} seconds")
        status, value = result["reply"]
        if status == 400 and images:
            raise ReasonerUnavailable("no_vision", f"{self.label} ({self.model}) wouldn't take the attached images. Choose a model that reads images: chaser model")
        if status == 402:
            raise self._refuse("out_of_credits", f"{self.label} is out of credits. Top up to keep using it.")
        if status in {401, 403}:
            raise self._refuse("not_authorised", f"{self.label} refused this machine's key (HTTP {status}).")
        if status == 409 and self.reasoner_id == "chaseos-cloud":
            from chaser_agent.cloud_key import PLAN_PROBLEM

            raise self._refuse("plan", f"{PLAN_PROBLEM} (HTTP 409)")
        if status != 200:
            # Keep the gateway's own explanation (e.g. a 409 plan or allowance conflict) instead of only the number.
            error = value.get("error") if isinstance(value, dict) else None
            said = (error.get("message") if isinstance(error, dict) else error if isinstance(error, str) else None) or value.get("message")
            said = f": {str(said)[:240]}" if said else ""
            raise ReasonerUnavailable("route_error", f"{self.label} did not answer (HTTP {status or 'no connection'}){said}.")
        try:
            choice = value["choices"][0]["message"]
            text = choice.get("content") or ""
        except (KeyError, IndexError, TypeError, AttributeError):
            text = ""
        if not isinstance(text, str) or not text.strip():
            raise ReasonerUnavailable("bad_output", f"{self.label} returned no text")
        self.refused = None
        credits, usage = cloud_usage(value)
        return ReasonerReply(text, self.reasoner_id, str(value.get("model") or self.model), round(time.monotonic() - started, 3), credits, usage)


class OpenAICompatibleReasoner(ChaseOSCloudReasoner):
    """Any provider with an OpenAI-style chat API, chosen in `chaser model`: OpenRouter, OpenAI, Gemini, a local Ollama...

    Same loop, same JSON-mode request and the same rule as ChaseOS Cloud: a refusal or an empty balance stops the
    turn and says so; nothing switches provider behind the person's back. The key leaves the environment at start.
    """

    def __init__(self, provider_id: str, label: str, *, base_url: str, model: str, key: str = "", key_source: str = "",
                 needs_key: bool = True, max_tokens: int = 8000) -> None:
        super().__init__(key, model=model, base_url=base_url or "", max_tokens=max_tokens, key_source=key_source)
        self.base_url = (base_url or "").rstrip("/")
        self.reasoner_id = provider_id
        self.label = label
        self.needs_key = needs_key

    @classmethod
    def from_settings(cls, settings: dict[str, Any], environ: dict[str, str] | None = None) -> "OpenAICompatibleReasoner":
        from chaser_agent import model_providers as providers

        provider, model, base_url = providers.chosen(settings)
        environ = os.environ if environ is None else environ
        key, source = providers.load_key(provider.id, environ)
        if provider.key_env:
            environ.pop(provider.key_env, None)
        return cls(provider.id, provider.label, base_url=base_url, model=model, key=key, key_source=source, needs_key=provider.needs_key)

    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": CLOUD_USER_AGENT}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        return headers

    def status(self) -> dict[str, Any]:
        if self._refusal():
            return {"id": self.reasoner_id, "label": self.label, "available": False, "model": self.model, "reason": self._refusal()}
        return self._base_status()

    def _base_status(self) -> dict[str, Any]:
        missing = []
        if self.needs_key and not self._key:
            missing.append(f"No {self.label} key yet. Run: chaser model")
        if not self.base_url:
            missing.append("No address set for this endpoint. Run: chaser model")
        if not self.model:
            missing.append("No model chosen. Run: chaser model")
        return {"id": self.reasoner_id, "label": self.label, "available": not missing, "model": self.model,
                "reason": missing[0] if missing else None}


def _count(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def cloud_usage(value: dict[str, Any]) -> tuple[int | None, dict[str, Any] | None]:
    """What one gateway reply says it used and charged: token counts, credits, pricing profile and served model."""
    tokens = value.get("usage") if isinstance(value.get("usage"), dict) else {}
    meta = value.get("chaseos") if isinstance(value.get("chaseos"), dict) else {}
    pricing = meta.get("pricing") if isinstance(meta.get("pricing"), dict) else {}
    routing = meta.get("routing") if isinstance(meta.get("routing"), dict) else {}
    credits = _count(meta.get("actual_credits"))
    usage = {
        "prompt_tokens": _count(tokens.get("prompt_tokens")),
        "completion_tokens": _count(tokens.get("completion_tokens")),
        "cached_input_tokens": _count(tokens.get("cached_input_tokens")),
        "credits": credits,
        "pricing_profile": pricing.get("pricing_profile") if isinstance(pricing.get("pricing_profile"), str) else None,
        "resolved_model": meta.get("resolved_model") if isinstance(meta.get("resolved_model"), str) else None,
        "attempts": _count(routing.get("attempt_count")),
    }
    return credits, (usage if any(v is not None for v in usage.values()) else None)


BRIDGE_CONNECTED_SECONDS = 300


class BridgeReasoner:
    """Another harness answers over the local API. One waiter per request."""

    reasoner_id = "bridge"
    label = "Another harness over the local API"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}
        self._last_asked: float | None = None

    def status(self) -> dict[str, Any]:
        with self._lock:
            waiting = len(self._pending)
            connected = self._last_asked is not None and time.monotonic() - self._last_asked < BRIDGE_CONNECTED_SECONDS
        return {
            "id": self.reasoner_id, "label": self.label, "available": True, "connected": connected, "waiting_requests": waiting,
            "reason": None if connected else "No other program is answering right now, so work sent this way waits.",
        }

    def next_request(self) -> dict[str, Any] | None:
        """Offer a waiting request. One left unanswered too long is offered again, since its harness may have died."""
        now = time.monotonic()
        with self._lock:
            self._last_asked = now
            for request_id, row in self._pending.items():
                if row["offered_at"] is None or now - row["offered_at"] >= BRIDGE_LEASE_SECONDS:
                    row["offered_at"] = now
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
            self._pending[request_id] = {"system": system, "transcript": transcript, "ready": ready, "offered_at": None}
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
