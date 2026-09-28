"""One foreground lifecycle for the local HTTP service and desktop HUD.

This launcher owns only its own server thread and HUD. It does not attach a
computer-use executor, start voice input, or grant additional authority.
"""

from __future__ import annotations

import http.client
import json
import threading
import time
from pathlib import Path

from chaser_agent.hud_window import HudWindow
from chaser_agent.local_http import create_server, load_or_create_token


def _wait_for_server(port: int, worker: threading.Thread, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not worker.is_alive():
            raise RuntimeError("Local HTTP server stopped before the HUD opened")
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
        try:
            connection.request("GET", "/v1/health")
            response = connection.getresponse()
            health = json.load(response)
            if (response.status == 200 and health.get("service") == "chaser-agent"
                    and health.get("bind") == "127.0.0.1" and health.get("port") == port):
                return
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        finally:
            connection.close()
        time.sleep(0.05)
    raise RuntimeError("Local HTTP server did not answer its loopback health check")


def run_desktop(*, data_dir: Path, port: int = 8765,
                allowed_origins: tuple[str, ...] = (),
                voice_library: Path | None = None,
                voice_model_dir: Path | None = None) -> int:
    """Start one private local API and HUD; close both when the window exits."""
    token, token_path = load_or_create_token(data_dir)
    server = create_server(
        data_dir=data_dir, token=token, port=port,
        allowed_origins=allowed_origins, voice_library=voice_library,
    )
    try:
        window = HudWindow(
            port=server.server_port, token_file=token_path, show_idle=True,
            voice_model_dir=voice_model_dir, voice_output_enabled=voice_library is not None,
        )
    except BaseException:
        server.server_close()
        raise

    worker = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.25},
        name="chaser-local-http", daemon=True,
    )
    try:
        worker.start()
        _wait_for_server(server.server_port, worker)
        print(f"Chaser Agent local API: http://127.0.0.1:{server.server_port}/v1/health")
        print(f"Bearer token file: {token_path}")
        print("Desktop HUD is waiting for an authorized computer-use session; none is attached by this launcher.")
        if voice_model_dir is not None:
            print("Optional push-to-talk panel configured; microphone remains off until Talk is pressed.")
        print("Close the HUD window or press Ctrl+C here to stop this local API.")
        try:
            window.run()
        except KeyboardInterrupt:
            pass
    finally:
        try:
            if worker.is_alive():
                server.shutdown()
                worker.join(timeout=5)
        finally:
            server.server_close()
            window.close()
    if worker.is_alive():
        raise RuntimeError("Local HTTP server did not stop within five seconds")
    return server.server_port
