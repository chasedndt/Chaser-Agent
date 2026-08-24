from __future__ import annotations

import os
from pathlib import Path


# pytest's `pythonpath = ["src"]` config updates the current interpreter only.
# CLI tests launch child Python processes, so give those children the same
# clean-checkout import path without requiring an editable install.
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
existing = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = os.pathsep.join(
    part for part in (str(SRC_ROOT), existing) if part
)
