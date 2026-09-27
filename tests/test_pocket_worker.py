"""Path-boundary checks for the private warm speech protocol."""

from pathlib import Path

import pytest

from chaser_agent.pocket_worker import job_paths


VOICE_ID = "voice-20260927T135243892608Z-1c8319f9fb34"


def test_worker_accepts_only_a_fresh_job_in_its_output_root(tmp_path: Path):
    folder = tmp_path / VOICE_ID
    folder.mkdir()
    script = folder / "script.txt"
    script.write_text("Public toy line", encoding="utf-8")
    assert job_paths(tmp_path, VOICE_ID) == (script, folder / "response.wav", folder / "response.json")
    (folder / "response.wav").write_bytes(b"existing")
    with pytest.raises(ValueError, match="already has output"):
        job_paths(tmp_path, VOICE_ID)


@pytest.mark.parametrize("voice_id", ["../control-token", "voice-20260927T135243892608Z-1c8319f9fb34/..", "other"])
def test_worker_rejects_path_traversal_and_unlisted_ids(tmp_path: Path, voice_id: str):
    with pytest.raises(ValueError, match="Invalid voice job ID"):
        job_paths(tmp_path, voice_id)
