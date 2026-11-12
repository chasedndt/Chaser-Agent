"""Settings routes for the HUD: the Cloud key, the pre-flight checks, your name and the shortcuts.

Mounted under /v1/agent/setup, behind the same loopback, origin and token checks as every agent
route. A key goes in and is never sent back: replies say only whether one is saved and in use.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlsplit

from chaser_agent import chaser_home, cloud_key, setup_checks, shortcuts

PREFIX = "/v1/agent/setup"
POSTS = {f"{PREFIX}/key", f"{PREFIX}/key/remove", f"{PREFIX}/profile", f"{PREFIX}/shortcuts"}
MAX_REVIEWER = 60


def _cloud(runtime: Any) -> Any:
    return runtime.reasoners.get("chaseos-cloud")


def _key_state(runtime: Any) -> dict[str, Any]:
    cloud = _cloud(runtime)
    source = getattr(cloud, "key_source", "none") if cloud is not None else "none"
    return {"in_use": cloud is not None and source != "none", "source": source, "saved": cloud_key.path().is_file()}


def overview(runtime: Any, port: int) -> dict[str, Any]:
    settings = chaser_home.load()
    return {
        "onboarded": bool(settings.get("onboarded_at")), "reviewer": settings.get("reviewer") or "",
        "data_dir": str(runtime.data_dir), "port": port, "key": _key_state(runtime),
        "shortcuts": shortcuts.overview(settings["shortcuts"]),
        "shortcuts_note": "Chaser holds these keys once it can use the mouse and keyboard. Until then they're kept free for it.",
    }


def handle_get(handler: Any, runtime: Any) -> bool:
    parts = urlsplit(handler.path)
    port = handler.server.server_port
    if parts.path == PREFIX:
        handler._reply(200, overview(runtime, port))
        return True
    if parts.path == f"{PREFIX}/checks":
        online = (parse_qs(parts.query).get("online") or ["0"])[0] == "1"
        cloud = _cloud(runtime)
        running = {"port": port, "key_source": getattr(cloud, "key_source", "none"), "key": getattr(cloud, "_key", "")}
        handler._reply(200, setup_checks.run({**chaser_home.load(), "data_dir": str(runtime.data_dir), "port": port}, online=online, running=running))
        return True
    return False


def handle_post(handler: Any, runtime: Any, request: dict[str, Any]) -> None:
    route = urlsplit(handler.path).path
    port = handler.server.server_port
    try:
        if route == f"{PREFIX}/key":
            if set(request) - {"key", "check"}:
                raise ValueError("Unsupported fields")
            key = cloud_key.validate(str(request.get("key") or ""))
            result = cloud_key.check(key) if request.get("check", True) else {"ok": None}
            if result.get("refused"):
                handler._reply(400, {"error": {"code": "key_refused", "message": result["reason"]}})
                return
            cloud_key.save(key)
            cloud = _cloud(runtime)
            if cloud is not None:
                cloud.set_key(key, source="saved")
            runtime.refresh_routes()
            handler._reply(200, {"key": _key_state(runtime), "check": {k: v for k, v in result.items() if k != "refused"}})
            return
        if route == f"{PREFIX}/key/remove":
            removed = cloud_key.forget()
            cloud = _cloud(runtime)
            if cloud is not None and cloud.key_source == "saved":
                cloud.set_key("")
            runtime.refresh_routes()
            handler._reply(200, {"removed": removed, "key": _key_state(runtime)})
            return
        if route == f"{PREFIX}/profile":
            if set(request) - {"reviewer", "onboarded"}:
                raise ValueError("Unsupported fields")
            changes: dict[str, Any] = {}
            if "reviewer" in request:
                reviewer = " ".join(str(request["reviewer"] or "").split())
                if len(reviewer) > MAX_REVIEWER:
                    raise ValueError(f"Keep the name under {MAX_REVIEWER} characters")
                changes["reviewer"] = reviewer
            if request.get("onboarded"):
                from datetime import UTC, datetime

                changes["onboarded_at"] = datetime.now(UTC).isoformat(timespec="seconds")
            chaser_home.save(changes)
            handler._reply(200, overview(runtime, port))
            return
        if route == f"{PREFIX}/shortcuts":
            if request.get("reset"):
                chaser_home.save({"shortcuts": dict(chaser_home.DEFAULT_SHORTCUTS)})
            else:
                name = str(request.get("name") or "")
                chosen = chaser_home.load()["shortcuts"]
                chaser_home.save({"shortcuts": {name: shortcuts.check_choice(name, str(request.get("chord") or ""), chosen)}})
            handler._reply(200, overview(runtime, port))
            return
        handler._error(404, "not_found", "Route not found")
    except cloud_key.KeyStoreUnavailable as exc:
        handler._error(409, "key_store_unavailable", str(exc))
    except (ValueError, OSError) as exc:
        handler._error(400, "invalid_input", str(exc))
