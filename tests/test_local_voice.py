"""Offline Pocket Alba adapter contracts; no real model is loaded here."""

from __future__ import annotations

import hashlib
import json
import queue
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from chaser_agent.local_voice import PocketAlbaVoice, VoiceBusy, WarmPocketAlbaVoice, stop_owned_process


@pytest.fixture
def library(tmp_path: Path, monkeypatch):
    root = tmp_path / "library"
    root.mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    python = runtime / "python.exe"
    config = runtime / "english-public-local.yaml"
    preset = runtime / "alba.safetensors"
    for path in (python, config, preset):
        path.write_text("test placeholder", encoding="utf-8")
    (root / "Speech.ps1").write_text("test placeholder", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "speech.py").write_text("test placeholder", encoding="utf-8")
    (root / "voice-library.json").write_text(
        json.dumps({
            "chaser_agent_production_voice": {
                "voice_id": "pocket-alba", "status": "operator-approved canonical production voice"
            },
            "voices": [{"id": "pocket-alba", "production_root": str(runtime)}],
            "runtime_paths": {
                "pocket_python": str(python), "pocket_config": str(config), "pocket_voices": str(runtime)
            },
        }), encoding="utf-8",
    )
    return root


def test_local_voice_uses_fixed_preset_offline_and_retains_receipt(library, tmp_path, monkeypatch):
    wav_body = b"RIFF" + b"a" * 64

    def fake_popen(command, **kwargs):
        assert command[command.index("--voice") + 1] == "pocket-alba"
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        assert not kwargs.get("shell", False)
        text = Path(command[command.index("--text-file") + 1])
        assert text.read_text(encoding="utf-8") == "Hello from a public toy run."
        wav = Path(command[command.index("--output") + 1])

        class FakeProcess:
            returncode = 0

            def communicate(self, timeout=None):
                wav.write_bytes(wav_body)
                wav.with_suffix(".json").write_text(
                    json.dumps({"voice_id": "pocket-alba", "sha256": hashlib.sha256(wav_body).hexdigest(), "duration_seconds": 1.0}),
                    encoding="utf-8",
                )
                return "", ""

            def poll(self):
                return self.returncode

        return FakeProcess()

    monkeypatch.setattr("chaser_agent.local_voice.subprocess.Popen", fake_popen)
    adapter = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    queued = adapter.enqueue("Hello from a public toy run.")
    assert queued["status"] == "queued"
    adapter._worker_thread.join(timeout=5)
    result = adapter.status(queued["voice_id"])
    assert result["status"] == "generated_pending_listening_review"
    assert result["sha256"] == hashlib.sha256(wav_body).hexdigest()
    assert adapter.audio_path(result["voice_id"]).read_bytes() == wav_body
    assert adapter.audio_path("../control-token") is None
    restarted = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    assert restarted.status(result["voice_id"])["status"] == "generated_pending_listening_review"


def test_voice_busy_and_failed_generation_are_not_successes(library, tmp_path, monkeypatch):
    adapter = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    adapter._generation_lock.acquire()
    try:
        with pytest.raises(VoiceBusy):
            adapter.enqueue("Hello")
    finally:
        adapter._generation_lock.release()
    monkeypatch.setattr(
        "chaser_agent.local_voice.subprocess.Popen",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, communicate=lambda timeout: ("", "")),
    )
    queued = adapter.enqueue("Hello")
    adapter._worker_thread.join(timeout=5)
    assert adapter.status(queued["voice_id"])["status"] == "failed"


def test_cancel_active_take_blocks_late_audio_even_after_restart(library, tmp_path, monkeypatch):
    adapter = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    started = threading.Event()
    release = threading.Event()
    stopped = threading.Event()
    wav_body = b"RIFF" + b"c" * 64

    class FakeProcess:
        def poll(self):
            return None

    process = FakeProcess()

    def fake_generate(voice_id):
        with adapter._state_lock:
            adapter._process = process
        started.set()
        assert release.wait(3)
        folder = adapter.voice_root / voice_id
        (folder / "response.wav").write_bytes(wav_body)
        (folder / "response.json").write_text(json.dumps({
            "voice_id": "pocket-alba", "sha256": hashlib.sha256(wav_body).hexdigest(),
            "duration_seconds": 1.0,
        }), encoding="utf-8")
        return adapter._verified_take(voice_id)

    monkeypatch.setattr(adapter, "_generate", fake_generate)
    monkeypatch.setattr("chaser_agent.local_voice.stop_owned_process", lambda candidate: stopped.set() if candidate is process else None)
    queued = adapter.enqueue("Public toy take to cancel")
    assert started.wait(3)
    cancelling = adapter.cancel(queued["voice_id"])
    assert cancelling["status"] == "cancelling"
    assert stopped.wait(3)
    assert adapter.status(queued["voice_id"])["status"] == "cancelling"
    release.set()
    adapter._worker_thread.join(timeout=5)
    assert adapter.status(queued["voice_id"])["status"] == "cancelled"
    assert adapter.audio_path(queued["voice_id"]) is None
    assert adapter.cancel(queued["voice_id"])["status"] == "cancelled"
    assert adapter.cancel("../control-token") is None
    restarted = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    assert restarted.status(queued["voice_id"])["status"] == "cancelled"
    assert restarted.audio_path(queued["voice_id"]) is None


def test_cancel_before_worker_starts_skips_generation(library, tmp_path, monkeypatch):
    adapter = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    entered = threading.Event()
    release = threading.Event()
    generated = []
    original_run = adapter._run_job

    def delayed_run(voice_id):
        entered.set()
        assert release.wait(3)
        original_run(voice_id)

    monkeypatch.setattr(adapter, "_run_job", delayed_run)
    monkeypatch.setattr(adapter, "_generate", lambda voice_id: generated.append(voice_id))
    queued = adapter.enqueue("Public toy take")
    assert entered.wait(3)
    assert adapter.cancel(queued["voice_id"])["status"] == "cancelling"
    release.set()
    adapter._worker_thread.join(timeout=5)
    assert generated == []
    assert adapter.status(queued["voice_id"])["status"] == "cancelled"


def test_voice_refuses_unapproved_identity(library, tmp_path):
    manifest_path = library / "voice-library.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chaser_agent_production_voice"]["voice_id"] = "other"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Pocket Alba"):
        PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")


def test_voice_close_terminates_only_its_active_process(library, tmp_path):
    adapter = PocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")

    class ActiveProcess:
        terminated = False

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout):
            return 1

    process = ActiveProcess()
    adapter._process = process
    adapter.close()
    assert process.terminated


def test_warm_worker_reuses_one_local_model_process_for_two_takes(library, tmp_path, monkeypatch):
    processes = []
    wav_body = b"RIFF" + b"z" * 64

    class FakeWorker:
        def __init__(self, command, **kwargs):
            assert "pocket_worker.py" in command[2]
            assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
            self.requests = queue.Queue()
            self.root = Path(command[command.index("--output-root") + 1])
            self.stdin = self
            self.stdout = self.lines()
            self.terminated = False
            processes.append(self)

        def lines(self):
            yield '{"event":"ready"}\n'
            while True:
                voice_id = self.requests.get(timeout=5)
                if voice_id is None:
                    break
                wav = self.root / voice_id / "response.wav"
                wav.write_bytes(wav_body)
                wav.with_suffix(".json").write_text(
                    json.dumps({"voice_id": "pocket-alba", "sha256": hashlib.sha256(wav_body).hexdigest(), "duration_seconds": 1.0}),
                    encoding="utf-8",
                )
                yield json.dumps({"event": "done", "voice_id": voice_id}) + "\n"

        def write(self, line):
            self.requests.put(json.loads(line)["voice_id"])

        def flush(self):
            pass

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            self.terminated = True
            self.requests.put(None)

        def wait(self, timeout):
            return 0

    monkeypatch.setattr("chaser_agent.local_voice.subprocess.Popen", FakeWorker)
    adapter = WarmPocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    adapter.prewarm()
    adapter._worker_thread.join(timeout=5)
    assert adapter.runtime_state() == "ready"
    first = adapter.enqueue("First public toy response")
    adapter._worker_thread.join(timeout=5)
    assert adapter.status(first["voice_id"])["status"] == "generated_pending_listening_review"
    second = adapter.enqueue("Second public toy response")
    adapter._worker_thread.join(timeout=5)
    assert adapter.status(second["voice_id"])["status"] == "generated_pending_listening_review"
    assert len(processes) == 1
    adapter.close()
    assert processes[0].terminated
    assert adapter.runtime_state() == "closed"


def test_warm_worker_cancel_releases_busy_slot_and_later_take_recovers(library, tmp_path, monkeypatch):
    processes = []
    first_generating = threading.Event()
    wav_body = b"RIFF" + b"r" * 64

    class FakeWorker:
        def __init__(self, command, **_kwargs):
            self.index = len(processes)
            self.requests = queue.Queue()
            self.stopped = threading.Event()
            self.root = Path(command[command.index("--output-root") + 1])
            self.stdin = self
            self.stdout = self.lines()
            processes.append(self)

        def lines(self):
            yield '{"event":"ready"}\n'
            while not self.stopped.is_set():
                voice_id = self.requests.get(timeout=5)
                if voice_id is None:
                    break
                if self.index == 0:
                    first_generating.set()
                    assert self.stopped.wait(3)
                    break
                wav = self.root / voice_id / "response.wav"
                wav.write_bytes(wav_body)
                wav.with_suffix(".json").write_text(json.dumps({
                    "voice_id": "pocket-alba", "sha256": hashlib.sha256(wav_body).hexdigest(),
                    "duration_seconds": 1.0,
                }), encoding="utf-8")
                yield json.dumps({"event": "done", "voice_id": voice_id}) + "\n"

        def write(self, line):
            self.requests.put(json.loads(line)["voice_id"])

        def flush(self):
            pass

        def poll(self):
            return 0 if self.stopped.is_set() else None

        def terminate(self):
            self.stopped.set()
            self.requests.put(None)

        def wait(self, timeout):
            return 0

    monkeypatch.setattr("chaser_agent.local_voice.subprocess.Popen", FakeWorker)
    monkeypatch.setattr("chaser_agent.local_voice.stop_owned_process", lambda process: process.terminate())
    adapter = WarmPocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    adapter.prewarm()
    adapter._worker_thread.join(timeout=5)
    assert adapter.runtime_state() == "ready"
    first = adapter.enqueue("First public toy response")
    assert first_generating.wait(3)
    assert adapter.cancel(first["voice_id"])["status"] == "cancelling"
    adapter._worker_thread.join(timeout=5)
    assert adapter.status(first["voice_id"])["status"] == "cancelled"
    assert adapter.audio_path(first["voice_id"]) is None
    second = adapter.enqueue("Second public toy response")
    adapter._worker_thread.join(timeout=5)
    assert adapter.status(second["voice_id"])["status"] == "generated_pending_listening_review"
    assert len(processes) == 2
    adapter.close()


def test_stop_owned_process_targets_only_the_known_windows_child_tree(monkeypatch):
    if __import__("os").name != "nt":
        pytest.skip("Windows process-tree supervision")
    calls = []

    class Process:
        pid = 41234
        alive = True

        def poll(self):
            return None if self.alive else 0

        def wait(self, timeout):
            return 0

        def terminate(self):
            self.alive = False

    process = Process()

    def fake_taskkill(command, **kwargs):
        calls.append(command)
        process.alive = False
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("chaser_agent.local_voice.subprocess.run", fake_taskkill)
    stop_owned_process(process)
    assert calls == [["taskkill", "/T", "/F", "/PID", "41234"]]


def test_startup_diagnostics_are_bounded_copied_and_content_free(library, tmp_path, monkeypatch):
    adapter = WarmPocketAlbaVoice(library_root=library, data_dir=tmp_path / "data")
    assert adapter.startup_diagnostics() == {"milestones_seconds": {}}
    adapter._startup_started = 10.0
    adapter._events = queue.Queue()
    for stage in ("starting", "libraries_loaded", "model_loaded", "ready"):
        adapter._events.put({"event": stage, "text": "not telemetry"})
    monkeypatch.setattr("chaser_agent.local_voice.time.monotonic", lambda: 12.0)
    assert adapter._await_event(timeout=10)["event"] == "ready"
    result = adapter.startup_diagnostics()
    assert result == {"milestones_seconds": {
        "starting": 2.0, "libraries_loaded": 2.0, "model_loaded": 2.0, "ready": 2.0,
    }}
    result["milestones_seconds"].clear()
    assert len(adapter.startup_diagnostics()["milestones_seconds"]) == 4
