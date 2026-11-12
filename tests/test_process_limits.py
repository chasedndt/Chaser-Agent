"""The memory ceiling really stops a runaway child, and leaves ordinary work alone."""

from __future__ import annotations

import subprocess
import sys

ALLOCATE = "import sys\ntry:\n    block = bytearray({mb} * 1024 * 1024)\nexcept MemoryError:\n    sys.exit(42)\nprint('ok')"


def _run(limit_mb: int, allocate_mb: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "chaser_agent.process_limits", "--process-mb", str(limit_mb), "--",
         sys.executable, "-c", ALLOCATE.format(mb=allocate_mb)],
        capture_output=True, text=True, timeout=90, check=False,
    )


def test_a_child_over_the_ceiling_cannot_allocate() -> None:
    assert _run(256, 1024).returncode == 42


def test_a_child_under_the_ceiling_runs_normally() -> None:
    done = _run(512, 16)
    assert done.returncode == 0
    assert done.stdout.strip() == "ok"


def test_limits_must_be_positive() -> None:
    from chaser_agent.process_limits import limit_memory

    try:
        limit_memory(process_mb=0)
    except ValueError:
        return
    raise AssertionError("A zero limit should be refused")
