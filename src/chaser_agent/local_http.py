"""Bounded loopback HTTP adapter for the deterministic, review-only harness.

This is not a public server, provider router, computer-use executor, or voice
adapter. It deliberately has no configurable non-loopback bind address.
"""

from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import threading
import time
from collections import deque
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from chaser_agent.hud_runtime import HudBridge, HudUnavailable
from chaser_agent.local_acl import assert_private_runtime_path
from chaser_agent.local_voice import MAX_SPEECH_CHARS, MAX_WAV_BYTES, WarmPocketAlbaVoice, VoiceBusy, VoiceGenerationFailed
from chaser_agent.run_artifacts import build_run_log, write_artifact_set
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import (
    build_source_card_artifacts,
    source_id_for_path,
    utc_now_iso,
)

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 262_144
MAX_TEXT_CHARS = 100_000
POSTS_PER_MINUTE = 20
ARTIFACT_NAMES = frozenset(
    {
        "source_card.json",
        "claims_table.json",
        "evidence_snippets.json",
        "uncertainty_labels.json",
        "action_candidates.json",
        "memory_candidates.json",
        "human_review_packet.json",
        "run_log.json",
        "original_source.md",
    }
)
PRIVACY_CLASSES = frozenset({"public_toy", "public"})
RUN_ID = re.compile(r"^source-card-http-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")


def load_or_create_token(data_dir: Path) -> tuple[str, Path]:
    """Keep the bearer token outside the repository and never print its value."""
    if data_dir.is_symlink():
        raise ValueError("Data directory must not be a symlink")
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    assert_private_runtime_path(data_dir)
    token_path = data_dir / "control-token"
    if token_path.is_symlink():
        raise ValueError("Token file must not be a symlink")
    if token_path.exists():
        assert_private_runtime_path(token_path)
    if not token_path.exists():
        token = secrets.token_hex(32)
        try:
            descriptor = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(descriptor, "w", encoding="ascii") as stream:
                stream.write(token + "\n")
    assert_private_runtime_path(token_path)
    token = token_path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise ValueError("Invalid local token file; refusing to start")
    return token, token_path


def validate_allowed_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != LOOPBACK_HOST
        or parsed.port is None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Allowed origins must be exact http://127.0.0.1:<port> URLs")
    return value


class SlidingWindowLimiter:
    def __init__(self, limit: int = POSTS_PER_MINUTE, interval: float = 60.0):
        self.limit = limit
        self.interval = interval
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.monotonic()
        with self._lock:
            while self._events and self._events[0] <= now - self.interval:
                self._events.popleft()
            if len(self._events) >= self.limit:
                return False
            self._events.append(now)
            return True


class LocalHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        *,
        data_dir: Path,
        token: str,
        port: int = DEFAULT_PORT,
        allowed_origins: tuple[str, ...] = (),
        voice_library: Path | None = None,
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", token):
            raise ValueError("A 256-bit hexadecimal bearer token is required")
        if not 0 <= port <= 65535:
            raise ValueError("Port must be between 0 and 65535")
        validated_origins = {validate_allowed_origin(value) for value in allowed_origins}
        if data_dir.is_symlink():
            raise ValueError("Data directory must not be a symlink")
        data_dir = data_dir.resolve()
        data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        assert_private_runtime_path(data_dir)
        self.data_dir = data_dir
        self.run_root = data_dir / "runs"
        self.run_root.mkdir(exist_ok=True, mode=0o700)
        assert_private_runtime_path(self.run_root)
        self.token = token
        self.limiter = SlidingWindowLimiter()
        self.hud = HudBridge()
        self.voice = WarmPocketAlbaVoice(library_root=voice_library, data_dir=data_dir) if voice_library else None
        if self.voice is not None:
            assert_private_runtime_path(self.voice.voice_root)
        super().__init__((LOOPBACK_HOST, port), LocalRequestHandler)
        self.allowed_origins = {f"http://{LOOPBACK_HOST}:{self.server_port}"}
        self.allowed_origins.update(validated_origins)
        if self.voice is not None:
            self.voice.prewarm()

    def server_close(self) -> None:
        try:
            self.hud.detach()
            if self.voice is not None:
                self.voice.close()
        finally:
            super().server_close()


class LocalRequestHandler(BaseHTTPRequestHandler):
    server: LocalHTTPServer
    server_version = "ChaserAgentLocal/0.1"
    sys_version = ""

    def setup(self) -> None:
        self.request.settimeout(10)
        super().setup()

    def log_message(self, _format: str, *args: object) -> None:
        # The default logger includes the raw request path. Source text and
        # bearer material must never accidentally reach a terminal log.
        return

    def _send_body(
        self,
        status: int,
        body: bytes,
        content_type: str,
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        origin = self.headers.get("Origin")
        if origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            # A client may disconnect while a bounded local operation finishes.
            # Do not print a traceback containing runtime paths or request state.
            self.close_connection = True

    def _reply(self, status: int, payload: dict[str, object], *, extra_headers: dict[str, str] | None = None) -> None:
        body = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        self._send_body(status, body, "application/json; charset=utf-8", extra_headers=extra_headers)

    def _error(self, status: int, code: str, message: str) -> None:
        self._reply(status, {"error": {"code": code, "message": message}})

    def _request_allowed(self) -> bool:
        if self.client_address[0] != LOOPBACK_HOST:
            self._error(403, "loopback_required", "Only loopback clients are accepted")
            return False
        if self.headers.get_all("Host", []) != [f"{LOOPBACK_HOST}:{self.server.server_port}"]:
            self._error(421, "invalid_host", "Use the configured loopback host and port")
            return False
        origins = self.headers.get_all("Origin", [])
        if len(origins) > 1:
            self._error(403, "invalid_origin", "Origin is not allowed")
            return False
        origin = origins[0] if origins else None
        if origin is not None and origin not in self.server.allowed_origins:
            self._error(403, "invalid_origin", "Origin is not allowed")
            return False
        return True

    def _authorized(self) -> bool:
        authorizations = self.headers.get_all("Authorization", [])
        provided = authorizations[0] if len(authorizations) == 1 else ""
        if hmac.compare_digest(provided, f"Bearer {self.server.token}"):
            return True
        if self.command == "POST":
            # On Windows, replying while a small body is still in flight can
            # abort the connection before the caller receives the 401. Drain
            # only a bounded declared body; never parse unauthenticated input.
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) == 1 and lengths[0].isdecimal() and int(lengths[0]) <= MAX_BODY_BYTES:
                try:
                    self.rfile.read(int(lengths[0]))
                except (TimeoutError, OSError):
                    pass
            self.close_connection = True
        self._reply(
            401,
            {"error": {"code": "unauthorized", "message": "Local bearer token required"}},
            extra_headers={"WWW-Authenticate": "Bearer"},
        )
        return False

    def do_OPTIONS(self) -> None:
        if not self._request_allowed():
            return
        if self.path not in {"/v1/source-cards", "/v1/voice/replies", "/v1/hud/controls"} or self.headers.get("Origin") not in self.server.allowed_origins:
            self._error(404, "not_found", "Route not found")
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:
        if not self._request_allowed():
            return
        if self.path == "/v1/health":
            self._reply(
                200,
                {
                    "service": "chaser-agent",
                    "status": "ready",
                    "bind": LOOPBACK_HOST,
                    "port": self.server.server_port,
                    "mode": "review_with_local_voice" if self.server.voice else "deterministic_review_only",
                    "hud": "executor_attached" if self.server.hud.snapshot()["controls_enabled"] else "not_connected",
                    "voice": "configured_local" if self.server.voice else "not_connected",
                    "voice_runtime": self.server.voice.runtime_state() if self.server.voice else "disabled",
                },
            )
            return
        if not self._authorized():
            return
        if self.path == "/v1/hud/current":
            self._reply(200, self.server.hud.snapshot())
            return
        segments = self.path.split("/")
        if len(segments) == 4 and segments[:3] == ["", "v1", "voice"]:
            adapter = self.server.voice
            status = adapter.status(segments[3]) if adapter else None
            if status is None:
                self._error(404, "not_found", "Voice take not found")
                return
            self._reply(200, status)
            return
        if len(segments) == 5 and segments[:3] == ["", "v1", "voice"] and segments[4] == "audio.wav":
            adapter = self.server.voice
            audio_path = adapter.audio_path(segments[3]) if adapter else None
            if audio_path is None:
                self._error(404, "not_found", "Voice take not found")
                return
            try:
                if audio_path.stat().st_size > MAX_WAV_BYTES:
                    raise OSError("WAV too large")
                audio_body = audio_path.read_bytes()
            except OSError:
                self._error(500, "audio_unavailable", "Voice take could not be read")
                return
            self._send_body(200, audio_body, "audio/wav")
            return
        if len(segments) not in {4, 6} or segments[:3] != ["", "v1", "runs"]:
            self._error(404, "not_found", "Route not found")
            return
        run_id = segments[3]
        if not RUN_ID.fullmatch(run_id):
            self._error(404, "not_found", "Run not found")
            return
        run_folder = self.server.run_root / run_id
        if not run_folder.is_dir() or run_folder.is_symlink():
            self._error(404, "not_found", "Run not found")
            return
        if len(segments) == 4:
            self._reply(200, {"run_id": run_id, "artifacts": sorted(ARTIFACT_NAMES), "review_status": "pending_review"})
            return
        if segments[4] != "artifacts" or segments[5] not in ARTIFACT_NAMES:
            self._error(404, "not_found", "Artifact not found")
            return
        artifact = run_folder / segments[5]
        if artifact.is_symlink() or not artifact.is_file():
            self._error(404, "not_found", "Artifact not found")
            return
        if artifact.name == "original_source.md":
            try:
                original = artifact.read_bytes()
            except OSError:
                self._error(500, "artifact_unavailable", "Artifact could not be read")
                return
            self._send_body(200, original, "text/markdown; charset=utf-8")
            return
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._error(500, "artifact_unavailable", "Artifact could not be read")
            return
        self._reply(200, payload)

    def do_POST(self) -> None:
        if not self._request_allowed():
            return
        if self.path not in {"/v1/source-cards", "/v1/voice/replies", "/v1/hud/controls"}:
            self._error(404, "not_found", "Route not found")
            return
        if not self._authorized():
            return
        if not self.server.limiter.allow():
            self._reply(429, {"error": {"code": "rate_limited", "message": "Try again later"}}, extra_headers={"Retry-After": "60"})
            return
        if self.headers.get("Transfer-Encoding") is not None:
            self._error(400, "invalid_body", "Transfer-Encoding is not supported")
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isdecimal():
            self._error(411, "length_required", "One Content-Length is required")
            return
        length = int(lengths[0])
        if length > MAX_BODY_BYTES:
            # Windows can reset a connection with unread request bytes before
            # the client receives 413. Drain only a small over-limit body;
            # never allocate or wait for an arbitrarily large declaration.
            if length <= MAX_BODY_BYTES + 8192:
                try:
                    self.rfile.read(length)
                except (TimeoutError, OSError):
                    pass
            self.close_connection = True
            self._error(413, "body_too_large", "Request exceeds the local size limit")
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            if length <= 8192:
                try:
                    self.rfile.read(length)
                except (TimeoutError, OSError):
                    pass
            else:
                self.close_connection = True
            self._error(415, "invalid_content_type", "Use application/json")
            return
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("Incomplete request body")

            def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
                result: dict[str, object] = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("Duplicate JSON key")
                    result[key] = value
                return result

            request = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates)
        except (UnicodeError, json.JSONDecodeError, ValueError, TimeoutError, OSError):
            self._error(400, "invalid_json", "A complete UTF-8 JSON object is required")
            return
        if not isinstance(request, dict):
            self._error(400, "invalid_input", "A JSON object is required")
            return
        if self.path == "/v1/hud/controls":
            self._post_hud_control(request)
            return
        if self.path == "/v1/voice/replies":
            self._post_voice_reply(request)
            return
        if set(request) - {"title", "text", "privacy_class", "profile"}:
            self._error(400, "invalid_input", "Unsupported source-card fields")
            return
        title = request.get("title")
        source_text = request.get("text")
        privacy_class = request.get("privacy_class", "public_toy")
        profile = request.get("profile", "general_source_review")
        if (
            not isinstance(title, str)
            or not 1 <= len(title.strip()) <= 200
            or not isinstance(source_text, str)
            or not 1 <= len(source_text.strip()) <= MAX_TEXT_CHARS
            or not isinstance(privacy_class, str)
            or privacy_class not in PRIVACY_CLASSES
            or not isinstance(profile, str)
        ):
            self._error(400, "invalid_input", "Title, text, profile or privacy class is invalid")
            return
        created_at = utc_now_iso()
        suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        run_id = f"source-card-http-{suffix}-{secrets.token_hex(6)}"
        run_folder = self.server.run_root / run_id
        stage_folder = self.server.run_root / f".pending-{run_id}"
        source_path = Path("original_source.md")
        source = SourceInput(
            id=source_id_for_path(source_path, source_text),
            title=title.strip(),
            text=source_text,
            source_type="note",
            source_origin="operator_submitted_local_http",
            privacy_class=privacy_class,
        )
        try:
            artifacts = build_source_card_artifacts(source, source_path, run_id, created_at, profile_id=profile)
            output_paths = [run_folder / name for name in [*artifacts, "run_log.json", "original_source.md"]]
            run_log = build_run_log(
                run_id=run_id,
                created_at=created_at,
                command="POST /v1/source-cards",
                input_source_id=source.id,
                output_paths=output_paths,
                repo_root=Path(__file__).resolve().parents[2],
            )
            write_artifact_set(stage_folder, artifacts, run_log)
            (stage_folder / "original_source.md").write_text(source_text, encoding="utf-8", newline="")
            stage_folder.rename(run_folder)
        except ValueError:
            self._error(400, "invalid_profile", "Workflow profile is unavailable for this source")
            return
        except OSError:
            self._error(500, "storage_error", "The local run could not be stored")
            return
        self._reply(
            201,
            {
                "run_id": run_id,
                "source_id": source.id,
                "review_status": "pending_review",
                "promotion_status": "not_promoted",
                "run_url": f"/v1/runs/{run_id}",
            },
        )

    def _post_voice_reply(self, request: dict[str, object]) -> None:
        if set(request) != {"text", "privacy_class"}:
            self._error(400, "invalid_input", "Voice replies require text and privacy_class only")
            return
        speech_text = request["text"]
        privacy_class = request["privacy_class"]
        if (
            not isinstance(speech_text, str)
            or not 1 <= len(speech_text.strip()) <= MAX_SPEECH_CHARS
            or not isinstance(privacy_class, str)
            or privacy_class not in PRIVACY_CLASSES
        ):
            self._error(400, "invalid_input", "Use 1–500 characters of public/toy text")
            return
        if self.server.voice is None:
            self._error(503, "voice_not_configured", "No local voice library was configured at startup")
            return
        try:
            result = self.server.voice.enqueue(speech_text)
        except VoiceBusy:
            self._error(409, "voice_busy", "Local voice is starting or generating another take")
            return
        except (VoiceGenerationFailed, OSError, ValueError):
            self._error(500, "voice_generation_failed", "No verified local voice take was produced")
            return
        self._reply(202, result, extra_headers={"Retry-After": "2"})

    def _post_hud_control(self, request: dict[str, object]) -> None:
        if set(request) != {"session_id", "command"}:
            self._error(400, "invalid_input", "Session ID and command are required")
            return
        session_id = request["session_id"]
        command = request["command"]
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 96 or not isinstance(command, str) or command not in {"pause", "resume", "stop", "take_over"}:
            self._error(400, "invalid_input", "Session ID or command is invalid")
            return
        request_id = f"hud-{secrets.token_hex(12)}"
        try:
            state = self.server.hud.request_control(session_id=session_id, request_id=request_id, command=command)
        except (HudUnavailable, ValueError):
            self._error(409, "hud_control_unavailable", "No matching active executor or control is unavailable")
            return
        status = "pending_executor_ack" if state.get("pending_id") == request_id else "acknowledged"
        self._reply(202, {"request_id": request_id, "status": status, "hud": state})


def create_server(
    *,
    data_dir: Path,
    token: str,
    port: int = DEFAULT_PORT,
    allowed_origins: tuple[str, ...] = (),
    voice_library: Path | None = None,
) -> LocalHTTPServer:
    return LocalHTTPServer(
        data_dir=data_dir,
        token=token,
        port=port,
        allowed_origins=allowed_origins,
        voice_library=voice_library,
    )
