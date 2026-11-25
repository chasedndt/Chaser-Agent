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
import re
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
    code, stdout, _ = _run_capturing(command, stdin=stdin, timeout=timeout, cancel=cancel, env=env, cwd=cwd, keep_stderr=False)
    return code, stdout


def _run_capturing(command: list[str], *, stdin: str, timeout: float, cancel: Event, env: dict[str, str] | None = None,
                   cwd: str | None = None, keep_stderr: bool = True) -> tuple[int, str, str]:
    """As _run_cancellable, also keeping stderr so a route can tell a used-up allowance from a fault. Never logged."""
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE if keep_stderr else subprocess.DEVNULL,
        encoding="utf-8", errors="replace", env=env, cwd=cwd, creationflags=NO_WINDOW,
    )
    result: dict[str, str] = {}

    def communicate() -> None:
        result["stdout"], result["stderr"] = process.communicate(stdin)

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
    return process.returncode, result.get("stdout") or "", result.get("stderr") or ""


# How the plan programs say an allowance is used up. Matched to classify the stop, never stored or shown.
_LIMIT_WORDS = re.compile(r"usage limit|limit reached|rate limit|too many requests|\b429\b|quota|out of credits|hit your limit", re.IGNORECASE)


def says_limit(text: str) -> bool:
    return bool(_LIMIT_WORDS.search(text or ""))


class ClaudeCliReasoner:
    """Claude Code's own CLI with every native tool off: it thinks, this loop acts."""

    reasoner_id = "claude-cli"
    label = "Claude (Claude Code login)"
    # A personal Claude plan: the guard keeps it to interactive tasks, never a headless job.
    route_kind = "plan"
    provider = "anthropic"

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
            if says_limit(detail):
                raise ReasonerUnavailable("plan_limit", "The Claude plan's usage limit is reached.")
            raise ReasonerUnavailable("route_error", detail)
        return ReasonerReply(text, self.reasoner_id, self.model, round(time.monotonic() - started, 3))


class HermesTextReasoner:
    """The existing zero-tool Hermes route on its own subscription. No fallback is added."""

    reasoner_id = "hermes-text"
    label = "Hermes (OpenAI subscription)"
    route_kind = "plan"
    provider = "openai"

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
# A route that is down (12 Nov 2026: chaseos/balanced answered 502 and 503 "the upstream provider failed" while
# chaseos/auto, fast and deep answered) is no reason to fail the owner's task: the next ChaseOS route is tried, still
# on ChaseOS Cloud and still in JSON mode. A 402 or a refused key never moves on.
CLOUD_FALLBACK_ENV = "CHASEOS_CLOUD_FALLBACK"
CLOUD_FALLBACK_DEFAULT = ("chaseos/deep", "chaseos/fast")
CLOUD_MOVE_ON_STATUSES = CLOUD_RETRY_STATUSES | {0, 409, 429, 500}


class OpenAICompatibleReasoner:
    """One chat-completions call to an OpenAI-compatible endpoint, in JSON mode, on a key held only in memory.

    The key is taken out of the environment when the service starts, so tools and other
    harnesses this service launches never inherit it."""

    reasoner_id = "openai-compatible"
    label = "OpenAI-compatible endpoint"
    route_kind = "api_key"
    provider = "unknown"
    max_context_chars = 120_000
    completions_path = "/chat/completions"

    def __init__(self, key: str = "", *, model: str, base_url: str, max_tokens: int = 8000, fallback: tuple[str, ...] = ()) -> None:
        self._key = key.strip()
        self.model = model
        self.fallback = tuple(m for m in fallback if m and m != model)
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens

    def status(self) -> dict[str, Any]:
        return {"id": self.reasoner_id, "label": self.label, "available": bool(self._key), "model": self.model,
                "reason": None if self._key else "No key is set for this route."}

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json", "User-Agent": CLOUD_USER_AGENT}

    def _post(self, body: bytes, timeout: float) -> tuple[int, dict[str, Any]]:
        import urllib.error
        import urllib.request

        request = urllib.request.Request(f"{self.base_url}{self.completions_path}", data=body, method="POST", headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - the owner's chosen endpoint
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                value = json.loads(exc.read().decode("utf-8", errors="replace") or "{}")
            except ValueError:
                value = {}
            return exc.code, value if isinstance(value, dict) else {}
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            return 0, {}

    def _failure(self, status: int, value: dict[str, Any]) -> ReasonerUnavailable:
        error = value.get("error") if isinstance(value.get("error"), dict) else {}
        said = error.get("message")
        if status == 402 or (status == 429 and error.get("code") == "insufficient_quota"):
            return ReasonerUnavailable("out_of_credits", f"{self.label} has no credit left with {self.provider}.")
        if status == 429:
            return ReasonerUnavailable("rate_limited", f"{self.label} is rate limited by {self.provider}.")
        if status in {401, 403}:
            return ReasonerUnavailable("not_authorised", f"{self.provider} refused the key (HTTP {status}).")
        return ReasonerUnavailable("route_error", f"{self.label} did not answer (HTTP {status or 'no connection'})."
                                   + (f" {str(said)[:200]}" if said else ""))

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        if not self._key:
            raise ReasonerUnavailable("not_configured", self.status()["reason"])
        started = time.monotonic()

        def body_for(model: str) -> bytes:
            return json.dumps({
                "model": model, "stream": False, "max_completion_tokens": self.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": transcript}],
                # Every reply must be one JSON object; without JSON mode the open models broke the format on about a third of steps.
                "response_format": {"type": "json_object"},
            }, ensure_ascii=False).encode("utf-8")
        body = body_for(self.model)
        result: dict[str, Any] = {}

        def call() -> None:
            deadline = started + timeout
            result["reply"] = self._post(body, max(1.0, deadline - time.monotonic()))
            # The gateway sometimes answers 502 and is fine a moment later, so one more try on the same route.
            if result["reply"][0] in CLOUD_RETRY_STATUSES | {0} and not cancel.is_set() and deadline - time.monotonic() > 5:
                time.sleep(1)
                result["reply"] = self._post(body, max(1.0, deadline - time.monotonic()))
            # Still down: one try on each fallback route, in order.
            for model in self.fallback:
                if result["reply"][0] not in CLOUD_MOVE_ON_STATUSES or cancel.is_set() or deadline - time.monotonic() <= 5:
                    break
                result["reply"] = self._post(body_for(model), max(1.0, deadline - time.monotonic()))

        worker = threading.Thread(target=call, daemon=True)
        worker.start()
        while worker.is_alive():
            worker.join(0.25)
            if cancel.is_set():
                raise ReasonerUnavailable("cancelled", "the operator cancelled this turn")
            if time.monotonic() - started > timeout + 5:
                raise ReasonerUnavailable("timeout", f"no reply within {int(timeout)} seconds")
        status, value = result["reply"]
        if status != 200:
            raise self._failure(status, value)
        try:
            choice = value["choices"][0]["message"]
            text = choice.get("content") or ""
        except (KeyError, IndexError, TypeError, AttributeError):
            text = ""
        if not isinstance(text, str) or not text.strip():
            raise ReasonerUnavailable("bad_output", f"{self.label} returned no text")
        credits, usage = cloud_usage(value)
        return ReasonerReply(text, self.reasoner_id, str(value.get("model") or self.model), round(time.monotonic() - started, 3), credits, usage)


class ChaseOSCloudReasoner(OpenAICompatibleReasoner):
    """ChaseOS Cloud: the route that never stops, metered in credits on the owner's own key.

    It takes a job when a plan's allowance runs out or the guard refuses a plan for it.
    A 402 means out of credits: Cloud is the last rung, so the turn stops and says so.
    """

    reasoner_id = "chaseos-cloud"
    label = "ChaseOS Cloud"
    route_kind = "cloud"
    provider = "chaseos"
    completions_path = "/v1/chat/completions"

    def __init__(self, key: str = "", *, model: str = "chaseos/balanced", base_url: str = "", max_tokens: int = 8000,
                 fallback: tuple[str, ...] = ()) -> None:
        super().__init__(key, model=model, base_url=base_url or CLOUD_BASE_URL, max_tokens=max_tokens, fallback=fallback)

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None, **kwargs: Any) -> "ChaseOSCloudReasoner":
        environ = os.environ if environ is None else environ
        key = environ.pop(CLOUD_KEY_ENV, "")
        base_url = kwargs.pop("base_url", "") or environ.get("CHASEOS_CLOUD_BASE_URL", "")
        # A different model, e.g. a candidate evaluated against an OpenAI-compatible endpoint.
        model = kwargs.pop("model", "") or environ.get("CHASEOS_CLOUD_MODEL", "") or "chaseos/balanced"
        raw = environ.get(CLOUD_FALLBACK_ENV)
        fallback = tuple(m.strip() for m in raw.split(",") if m.strip()) if raw is not None else CLOUD_FALLBACK_DEFAULT
        return cls(key, base_url=base_url, model=model, fallback=kwargs.pop("fallback", fallback), **kwargs)

    def status(self) -> dict[str, Any]:
        return {
            "id": self.reasoner_id, "label": self.label, "available": bool(self._key), "model": self.model,
            "reason": None if self._key else f"No ChaseOS Cloud key on this machine. Start the service with {CLOUD_KEY_ENV} set.",
        }

    def _headers(self) -> dict[str, str]:
        return {**super()._headers(), "X-ChaseOS-Agent-Harness": CLOUD_HARNESS}

    def _failure(self, status: int, value: dict[str, Any]) -> ReasonerUnavailable:
        if status == 402:
            return ReasonerUnavailable("out_of_credits", "ChaseOS Cloud is out of credits. Top up to keep using it.")
        if status in {401, 403}:
            return ReasonerUnavailable("not_authorised", f"ChaseOS Cloud refused this machine's key (HTTP {status}).")
        said = value.get("error", {}).get("message") if isinstance(value.get("error"), dict) else None
        return ReasonerUnavailable("route_error", f"ChaseOS Cloud did not answer (HTTP {status or 'no connection'})."
                                   + (f" {str(said)[:200]}" if said else ""))


API_KEY_ENV = "CHASER_API_KEY"
API_BASE_URL_ENV = "CHASER_API_BASE_URL"
API_MODEL_ENV = "CHASER_API_MODEL"
API_PROVIDER_ENV = "CHASER_API_PROVIDER"
API_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_PROVIDER_HOSTS = {"api.openai.com": "openai", "api.anthropic.com": "anthropic", "openrouter.ai": "openrouter",
                   "api.groq.com": "groq", "api.mistral.ai": "mistral", "api.deepseek.com": "deepseek",
                   "generativelanguage.googleapis.com": "google", "api.x.ai": "xai", "api.together.xyz": "together"}


def provider_for(base_url: str) -> str:
    from urllib.parse import urlsplit

    host = (urlsplit(base_url).hostname or "").lower()
    return _PROVIDER_HOSTS.get(host) or host or "unknown"


class ApiKeyReasoner(OpenAICompatibleReasoner):
    """The person's own API key for any provider with an OpenAI-compatible endpoint. Billed by that provider, allowed for any job."""

    reasoner_id = "own-api-key"
    label = "Your own API key"
    route_kind = "api_key"

    def __init__(self, key: str = "", *, model: str = "", base_url: str = "", provider: str = "", max_tokens: int = 8000) -> None:
        super().__init__(key, model=model, base_url=base_url or API_DEFAULT_BASE_URL, max_tokens=max_tokens)
        self.provider = provider or provider_for(self.base_url)

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None, **kwargs: Any) -> "ApiKeyReasoner":
        environ = os.environ if environ is None else environ
        key = environ.pop(API_KEY_ENV, "")
        return cls(key, model=kwargs.pop("model", "") or environ.get(API_MODEL_ENV, ""),
                   base_url=kwargs.pop("base_url", "") or environ.get(API_BASE_URL_ENV, ""),
                   provider=kwargs.pop("provider", "") or environ.get(API_PROVIDER_ENV, ""), **kwargs)

    def status(self) -> dict[str, Any]:
        reason = None
        if not self._key:
            reason = f"No API key of your own is set. Start the service with {API_KEY_ENV} (and {API_MODEL_ENV}, {API_BASE_URL_ENV})."
        elif not self.model:
            reason = f"Name the model for your API key with {API_MODEL_ENV}."
        return {"id": self.reasoner_id, "label": self.label, "available": reason is None, "provider": self.provider,
                "model": self.model or None, "reason": reason}

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        if not self.model:
            raise ReasonerUnavailable("not_configured", self.status()["reason"])
        return super().complete(system, transcript, timeout=timeout, cancel=cancel)


CODEX_EXECUTABLE_ENV = "CHASER_CODEX_EXECUTABLE"
CODEX_MODEL_ENV = "CHASER_CODEX_MODEL"
# Keys that would turn Codex onto an API key or another endpoint. The plan route runs on the ChatGPT sign-in only.
_CODEX_HIDDEN = frozenset({"OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL", "AZURE_OPENAI_API_KEY", API_KEY_ENV, CLOUD_KEY_ENV})
_CODEX_FLAGS = [
    "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
    "-c", 'model_provider="openai"', "-c", 'approval_policy="never"', "-c", 'web_search="disabled"',
    "-c", 'forced_login_method="chatgpt"',
    "-c", "features.shell_tool=false", "-c", "features.unified_exec=false", "-c", "features.apply_patch_freeform=false",
    "-c", "features.apps=false", "-c", "features.plugins=false", "-c", "features.multi_agent=false",
    "-c", "features.js_repl=false", "-c", "features.code_mode=false", "-c", "features.computer_use=false",
    "-c", "features.browser_use=false", "-c", "features.in_app_browser=false", "-c", "features.hooks=false",
    "-c", "features.skip_host_skill_discovery=true", "-c", "features.image_generation=false",
]
_CODEX_PACKAGES = r"Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\Repository\Packages"


def _installed_codex() -> str | None:
    """codex.exe inside the newest installed Codex desktop app (a Microsoft Store package), from the per-user registry.

    The package folder is named after the app's version, so every update moves it and a written-down path goes stale."""
    try:
        import winreg
    except ImportError:
        return None
    found: list[tuple[tuple[int, ...], str]] = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _CODEX_PACKAGES) as packages:
            index = 0
            while True:
                try:
                    name = winreg.EnumKey(packages, index)
                except OSError:
                    break
                index += 1
                if not name.startswith("OpenAI.Codex_"):
                    continue
                try:
                    with winreg.OpenKey(packages, name) as package:
                        root = winreg.QueryValueEx(package, "PackageRootFolder")[0]
                    version = tuple(int(part) for part in name[len("OpenAI.Codex_"):].split("_")[0].split("."))
                except (OSError, ValueError):
                    continue
                exe = Path(root) / "app" / "resources" / "codex.exe"
                if exe.is_file():
                    found.append((version, str(exe)))
    except OSError:
        return None
    return max(found)[1] if found else None


def find_codex() -> str | None:
    """The Codex CLI to run: a named one first, then one on PATH, then the installed desktop app's own copy."""
    return os.environ.get(CODEX_EXECUTABLE_ENV) or shutil.which("codex") or _installed_codex()


class CodexPlanReasoner:
    """The person's own ChatGPT plan, through their own Codex CLI on this computer, with every native tool off.

    Codex keeps its own sign-in. This route never reads, copies or sends it: it runs `codex exec`
    as the person would, with API keys taken out of its environment so it can only use the plan.
    When the plan's limit is reached it says so, and the ladder moves the job on to a key or Cloud.
    """

    reasoner_id = "codex-plan"
    label = "ChatGPT plan (Codex sign-in)"
    route_kind = "plan"
    provider = "openai"
    max_context_chars = 110_000

    def __init__(self, model: str = "", command: list[str] | None = None) -> None:
        self.model = model or None
        if command is None:
            executable = find_codex()
            command = [executable] if executable else []
        self.command = list(command)
        self._status: dict[str, Any] | None = None
        self._status_at = 0.0

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None) -> "CodexPlanReasoner":
        environ = os.environ if environ is None else environ
        return cls(model=environ.get(CODEX_MODEL_ENV, ""))

    @staticmethod
    def _environment() -> dict[str, str]:
        return {key: value for key, value in os.environ.items()
                if key.upper() not in _CODEX_HIDDEN and key not in _HARNESS_NAMES and not key.startswith(_HARNESS_PREFIXES)}

    def status(self) -> dict[str, Any]:
        if self._status is not None and time.monotonic() - self._status_at < 60:
            return self._status
        state: dict[str, Any] = {"id": self.reasoner_id, "label": self.label, "model": self.model}
        if not self.command:
            state.update(available=False, reason="Codex is not installed. Install it, then run: codex login")
        else:
            try:
                done = subprocess.run([*self.command, "login", "status"], capture_output=True, encoding="utf-8", errors="replace",
                                      timeout=45, env=self._environment(), creationflags=NO_WINDOW)
                said = (done.stdout + done.stderr).lower()
                if done.returncode == 0 and "chatgpt" in said:
                    state.update(available=True, reason=None)
                elif done.returncode == 0 and "api key" in said:
                    state.update(available=False, reason="Codex is signed in with an API key, not a ChatGPT plan.")
                else:
                    state.update(available=False, reason="Codex is not signed in with ChatGPT. Run: codex login")
            except (OSError, subprocess.SubprocessError):
                state.update(available=False, reason="Codex could not be asked whether it is signed in.")
        self._status, self._status_at = state, time.monotonic()
        return state

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        if not self.command:
            raise ReasonerUnavailable("not_installed", "Codex is not installed")
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="chaser-codex-") as folder:
            output = Path(folder) / "answer.txt"
            model = ["--model", self.model] if self.model else []
            code, stdout, stderr = _run_capturing(
                [*self.command, *_CODEX_FLAGS, *model, "--output-last-message", str(output), "-"],
                stdin=system + "\n\nReturn only the requested reply. Use no native tools.\n\n" + transcript,
                timeout=timeout, cancel=cancel, env=self._environment(), cwd=folder,
            )
            text = output.read_text(encoding="utf-8").strip() if output.is_file() else ""
        if code or not text:
            # Codex's own words are only classified here; they're never stored, so nothing it prints reaches a receipt.
            if says_limit(stdout + "\n" + stderr):
                raise ReasonerUnavailable("plan_limit", "The ChatGPT plan's usage limit is reached.")
            raise ReasonerUnavailable("route_error", f"Codex could not answer (exit {code}). Check its ChatGPT sign-in and model access.")
        return ReasonerReply(text, self.reasoner_id, self.model or "codex-default", round(time.monotonic() - started, 3))


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
    route_kind = "bridge"
    provider = "external"

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
    route_kind = "test"
    provider = "scripted"

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
