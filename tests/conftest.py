"""Every test gets its own settings folder, so no test reads or writes this computer's real Chaser settings or key."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _own_chaser_home(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHASER_AGENT_HOME", str(tmp_path_factory.mktemp("chaser-home")))
    monkeypatch.delenv("CHASEOS_CLOUD_KEY", raising=False)
