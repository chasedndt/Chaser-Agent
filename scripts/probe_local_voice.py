"""Opt-in live public/toy speech probe. No microphone, playback or cloud calls.

By default creates two retained local takes: requests cancellation immediately
after queueing the first, then verifies a recovery take and its authenticated
WAV against the server receipt. Warm-only mode creates one take without cancel.
Run only against your own idle, voice-enabled loopback instance.
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from chaser_agent.local_acl import read_private_control_token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--confirm-toy-jobs", action="store_true", required=True)
    parser.add_argument("--mode", choices=("cancel-recover", "warm-only"), default="cancel-recover")
    args = parser.parse_args()
    token = read_private_control_token(args.data_dir)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base = f"http://127.0.0.1:{args.port}"

    def request(path, payload=None, *, auth=True):
        headers = {"Authorization": f"Bearer {token}"} if auth else {}
        data = None if payload is None else json.dumps(payload).encode()
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(base + path, data, headers)
        try:
            with opener.open(req, timeout=10) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def json_request(path, payload=None):
        code, body = request(path, payload)
        if code not in (200, 202):
            raise RuntimeError(f"Unexpected HTTP {code} for {path}")
        return json.loads(body)

    def wait_for(path, key, expected, timeout):
        deadline = time.monotonic() + timeout
        previous = None
        while time.monotonic() < deadline:
            result = json_request(path)
            state = result.get(key)
            if state != previous:
                print(json.dumps({"path": path, key: state}), flush=True)
                previous = state
            if state == expected:
                return result
            if state in {"failed", "interrupted", "closed", "disabled"}:
                raise RuntimeError(f"{path} reached {state}")
            time.sleep(0.25)
        raise TimeoutError(f"{path} did not reach {expected}")

    wait_for("/v1/health", "voice_runtime", "ready", 260)
    print(json.dumps({"initial_runtime": json_request("/v1/voice/runtime")}), flush=True)
    cancellation = {"tested": False}
    if args.mode == "cancel-recover":
        first = json_request("/v1/voice/replies", {
            "text": "This is a public test of cancelling local speech generation. " * 5,
            "privacy_class": "public_toy",
        })
        first_path = first["status_url"]
        cancel_started = time.monotonic()
        json_request(first_path + "/cancel", {})
        cancelled = wait_for(first_path, "status", "cancelled", 30)
        cancelled_in = round(time.monotonic() - cancel_started, 3)
        blocked_code, _ = request(first_path + "/audio.wav")
        if blocked_code != 404:
            raise RuntimeError(f"Cancelled audio unexpectedly returned HTTP {blocked_code}")
        cancellation = {
            "tested": True, "voice_id": cancelled["voice_id"],
            "seconds": cancelled_in, "audio_http": blocked_code,
        }

    # A cancelled warm worker may be cold. A new job is allowed to reload it;
    # wait only for the previous job to release its generation lock.
    deadline = time.monotonic() + 10
    while json_request("/v1/health")["voice_runtime"] in {"starting", "busy"}:
        if time.monotonic() >= deadline:
            raise TimeoutError("Cancelled job did not release the voice worker")
        time.sleep(0.1)
    started = time.monotonic()
    second = json_request("/v1/voice/replies", {
        "text": "Chaser Agent is running locally. Your review is still required.",
        "privacy_class": "public_toy",
    })
    result = wait_for(second["status_url"], "status", "generated_pending_listening_review", 380)
    code, wav = request(result["audio_url"])
    if code != 200 or wav[:4] != b"RIFF" or wav[8:12] != b"WAVE":
        raise RuntimeError("Recovery did not return a WAV")
    if hashlib.sha256(wav).hexdigest() != result["sha256"]:
        raise RuntimeError("Recovery audio does not match its receipt")
    unauthenticated, _ = request(result["audio_url"], auth=False)
    if unauthenticated != 401:
        raise RuntimeError("Unauthenticated audio access was not rejected")
    print(json.dumps({
        "mode": args.mode, "cancellation": cancellation, "voice_id": result["voice_id"],
        "response_seconds": round(time.monotonic() - started, 3),
        "wav_bytes": len(wav), "sha256": result["sha256"],
        "duration_seconds": result["duration_seconds"], "unauthenticated_http": unauthenticated,
        "microphone_opened": False, "audio_played": False,
        "human_listening_review": "pending",
        "runtime": json_request("/v1/voice/runtime"),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
