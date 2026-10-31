"""The agent's routes on the private loopback service.

Mounted on the same handler as the review API, so the loopback, Host, Origin and
bearer checks there apply first. The console page and the public mascot motions
load without a token; the console reads the token from its URL fragment, which is
never sent to a server, and every data route still requires it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from chaser_agent.agent.events import with_io_retry
from chaser_agent.agent.reasoners import BridgeReasoner
from chaser_agent.agent.runtime import AgentRuntime, Conflict, NotFound

CONSOLE_ROOT = Path(__file__).resolve().parent / "console"
MOTION_ROOT = Path(__file__).resolve().parents[2] / "brand" / "chaser-agent" / "releases" / "motion-v1.1.0"
CONSOLE_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/console/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/console/app.css": ("app.css", "text/css; charset=utf-8"),
}
# Inline styles and blob frames exist only for showing a saved brief in a sandboxed frame.
CONSOLE_CSP = "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; media-src 'self'; connect-src 'self'; frame-src blob:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
MOTION_FILE = re.compile(r"^/assets/motion/([a-z-]{3,24})\.(png|mp4)$")
SESSION_ROUTE = re.compile(r"^/v1/agent/sessions/(as-[0-9]{14}-[0-9a-f]{10})(?:/([a-z]+))?(?:/(.+))?$")
ARTIFACT_TYPES = {
    ".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8", ".jsonl": "text/plain; charset=utf-8",
}


def serve_public(handler: Any) -> bool:
    """Console page and approved motion assets. Returns True when it answered."""
    path = urlsplit(handler.path).path
    entry = CONSOLE_FILES.get(path)
    if entry is not None:
        target = CONSOLE_ROOT / entry[0]
        if not target.is_file():
            handler._error(404, "not_found", "The console is not installed")
            return True
        handler._send_body(200, with_io_retry(target.read_bytes), entry[1], extra_headers={"Content-Security-Policy": CONSOLE_CSP, "Referrer-Policy": "no-referrer"})
        return True
    match = MOTION_FILE.fullmatch(path)
    if match:
        target = MOTION_ROOT / f"{match.group(1)}.{match.group(2)}"
        if not target.is_file():
            handler._error(404, "not_found", "Motion not found")
            return True
        handler._send_body(
            200, with_io_retry(target.read_bytes), "image/png" if match.group(2) == "png" else "video/mp4",
            extra_headers={"Accept-Ranges": "none", "Cache-Control": "public, max-age=86400"},
        )
        return True
    return False


def _runtime(handler: Any) -> AgentRuntime | None:
    runtime = handler.server.agent
    if runtime is None:
        handler._error(503, "agent_not_configured", "The agent runtime is not configured on this server")
    return runtime


def handle_get(handler: Any) -> None:
    runtime = _runtime(handler)
    if runtime is None:
        return
    parts = urlsplit(handler.path)
    if parts.path == "/v1/agent/status":
        handler._reply(200, runtime.status())
        return
    if parts.path == "/v1/agent/sessions":
        handler._reply(200, {"sessions": runtime.list_sessions()})
        return
    if parts.path == "/v1/agent/reasoner/next":
        bridge = runtime.reasoners.get("bridge")
        request = bridge.next_request() if isinstance(bridge, BridgeReasoner) else None
        handler._reply(200, {"request": request})
        return
    match = SESSION_ROUTE.fullmatch(parts.path)
    if not match:
        handler._error(404, "not_found", "Route not found")
        return
    session_id, section, rest = match.groups()
    try:
        if section is None:
            handler._reply(200, runtime.snapshot(session_id))
        elif section == "events" and rest is None:
            query = parse_qs(parts.query)
            after = int((query.get("after") or ["0"])[0])
            handler._reply(200, {"events": runtime.events(session_id, after)})
        elif section == "artifacts" and rest is None:
            handler._reply(200, {"artifacts": runtime.artifacts(session_id)})
        elif section == "artifacts":
            target = runtime.artifact_path(session_id, rest)
            kind = ARTIFACT_TYPES.get(target.suffix.lower(), "application/octet-stream")
            handler._send_body(200, target.read_bytes(), kind)
        elif section == "outputs" and rest:
            handler._reply(200, runtime.output_text(session_id, rest))
        else:
            handler._error(404, "not_found", "Route not found")
    except NotFound:
        handler._error(404, "not_found", "Not found")
    except ValueError:
        handler._error(400, "invalid_input", "The request is invalid")


def is_agent_post(path: str) -> bool:
    route = urlsplit(path).path
    return route in {"/v1/agent/sessions", "/v1/agent/reasoner/reply"} or bool(SESSION_ROUTE.fullmatch(route))


def _text(request: dict[str, Any], name: str, *, required: bool = True) -> str | None:
    value = request.get(name)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def handle_post(handler: Any, request: dict[str, Any]) -> None:
    runtime = _runtime(handler)
    if runtime is None:
        return
    route = urlsplit(handler.path).path
    try:
        if route == "/v1/agent/sessions":
            if set(request) - {"message", "workflow", "reasoner", "title", "withhold_tools"}:
                raise ValueError("Unsupported session fields")
            withheld = request.get("withhold_tools", [])
            if not isinstance(withheld, list) or not all(isinstance(item, str) for item in withheld):
                raise ValueError("withhold_tools must be a list of tool ids")
            snapshot = runtime.create_session(
                _text(request, "message") or "",
                workflow_id=_text(request, "workflow", required=False),
                reasoner_id=_text(request, "reasoner", required=False) or "auto",
                title=_text(request, "title", required=False),
                withhold_tools=frozenset(withheld),
            )
            handler._reply(201, snapshot)
            return
        if route == "/v1/agent/reasoner/reply":
            bridge = runtime.reasoners.get("bridge")
            accepted = isinstance(bridge, BridgeReasoner) and bridge.reply(
                _text(request, "request_id") or "", _text(request, "text") or "", str(request.get("model") or "external")[:80],
            )
            if not accepted:
                handler._error(404, "not_found", "No reasoner request is waiting with that id")
                return
            handler._reply(202, {"accepted": True})
            return
        match = SESSION_ROUTE.fullmatch(route)
        if not match or match.group(3):
            handler._error(404, "not_found", "Route not found")
            return
        session_id, section, _ = match.groups()
        if section == "messages":
            handler._reply(202, runtime.send_message(session_id, _text(request, "message") or ""))
        elif section == "answers":
            handler._reply(202, runtime.answer(session_id, _text(request, "question_id") or "", _text(request, "answer") or ""))
        elif section == "approvals":
            decided_by = (_text(request, "decided_by", required=False) or "local_operator")[:120]
            handler._reply(202, runtime.decide(session_id, _text(request, "approval_id") or "", _text(request, "digest") or "", _text(request, "decision") or "", decided_by))
        elif section == "cancel":
            handler._reply(202, runtime.cancel(session_id))
        else:
            handler._error(404, "not_found", "Route not found")
    except NotFound:
        handler._error(404, "not_found", "Not found")
    except Conflict as exc:
        handler._error(409, "conflict", str(exc))
    except ValueError as exc:
        handler._error(400, "invalid_input", str(exc))
