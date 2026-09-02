"""Enforce the brand canon's naming rules across the repository.

`tests/test_brand_canon.py` locks the canon documents, the manifest fields, and
the selected reference image. It does not check that the repository actually
*uses* the canonical name — so the canon could be installed and correct while
every surface drifted away from it.

That is the failure mode this project keeps meeting: a stated guarantee with
nothing that would fail if it were violated. These tests make the naming canon
executable.

Scope note: historical records are deliberately excluded. Build logs, daily
notes, agent-activity entries, and documentation-history archives are dated
accounts of what was written at the time; rewriting them to match a later canon
would falsify the record rather than fix a surface.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "docs" / "brand" / "chaser-agent" / "CHASER-AGENT-CANON-SYNC-MANIFEST.json").read_text(
        encoding="utf-8"
    )
)
CANONICAL_NAME = MANIFEST["public_name"]  # "Chaser Agent"

# Surfaces a reader or user could reasonably treat as current product truth.
LIVE_DOC_ROOTS = ("docs", "brand")
LIVE_ROOT_FILES = (
    "README.md",
    "HANDOVER.md",
    "START_HERE.md",
    "NEXT_STEPS.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "TRADEMARKS.md",
)

# Dated records: excluded on purpose (see module docstring).
HISTORICAL_PARTS = ("logs", "07_LOGS", "99_ARCHIVE", "Documentation-History")

# Wrong casing of the product name. Matches "Chaser agent" but not "Chaser Agent",
# and not identifiers such as chaser_agent or chaser-agent.
MISCASED_NAME = re.compile(r"\bChaser agent\b")

# Names the canon forbids for the public product.
FORBIDDEN_PUBLIC_NAMES = (
    "Chase Agent",
    "Chaser West",
    "ChaserOS Agent",
    "ChaseOS Agent",
)


def _is_historical(path: Path) -> bool:
    return any(part in HISTORICAL_PARTS for part in path.parts)


def live_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in LIVE_DOC_ROOTS:
        files.extend(
            path
            for path in (ROOT / root).rglob("*.md")
            if not _is_historical(path.relative_to(ROOT))
        )
    files.extend(ROOT / name for name in LIVE_ROOT_FILES if (ROOT / name).exists())
    return sorted(files)


def _offenders(pattern: re.Pattern[str]) -> list[str]:
    hits: list[str] = []
    for path in live_markdown_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{path.relative_to(ROOT).as_posix()}:{number}")
    return hits


def test_canonical_name_is_capitalised_on_every_live_surface():
    offenders = _offenders(MISCASED_NAME)
    assert not offenders, (
        f"{len(offenders)} surface(s) use 'Chaser agent' instead of the canonical "
        f"{CANONICAL_NAME!r}: " + ", ".join(offenders[:20])
    )


def python_sources() -> list[Path]:
    files: list[Path] = []
    for root in ("src", "scripts", "tests"):
        files.extend(
            path
            for path in (ROOT / root).rglob("*.py")
            if "__pycache__" not in path.parts and path.name != Path(__file__).name
        )
    return sorted(files)


def test_canonical_name_is_capitalised_in_python_sources():
    """Generators and CLI help emit user-facing text too.

    Found the hard way: `scripts/export_test_matrix.py` wrote 'Chaser agent'
    into the generated test matrix, so every regeneration reintroduced drift
    that a markdown-only check would have kept re-flagging without ever
    explaining why.
    """
    offenders: list[str] = []
    for path in python_sources():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if MISCASED_NAME.search(line):
                offenders.append(f"{path.relative_to(ROOT).as_posix()}:{number}")
    assert not offenders, (
        "Python sources must emit the canonical product name: " + ", ".join(offenders[:20])
    )


# A forbidden name is only a violation when used AS the product name. Two uses
# are legitimate and must not be "fixed":
#
#   1. Negation - a document quoting the name in order to forbid it, exactly as
#      the canon does: Chaser Agent (not "Chase Agent").
#   2. ChaseOS subsystem compounds - ChaseOS genuinely owns components such as
#      the Agent Control Plane and Agent Skills Sentinel. The canon forbids
#      renaming the product, not naming ChaseOS internals.
#
# Flagging these would drive incorrect edits. The asymmetry matters: a check
# that is too aggressive corrupts correct documents, while one that is slightly
# permissive leaves a visible, reviewable line.
NEGATION_MARKERS = ("not ", "never", "do not", "instead of", "forbidden", "rename", "avoid")
CHASEOS_SUBSYSTEM_SUFFIXES = ("Control Plane", "Skills Sentinel", "Bus", "Registry")


def _is_legitimate_use(line: str, forbidden: str) -> bool:
    lowered = line.lower()
    if any(marker in lowered for marker in NEGATION_MARKERS):
        return True
    return any(f"{forbidden} {suffix}" in line for suffix in CHASEOS_SUBSYSTEM_SUFFIXES)


@pytest.mark.parametrize("forbidden", FORBIDDEN_PUBLIC_NAMES)
def test_forbidden_public_names_are_not_used_as_the_product_name(forbidden: str):
    """The canon's do-not-use list, enforced with documented exemptions."""
    pattern = re.compile(rf"\b{re.escape(forbidden)}\b")
    offenders: list[str] = []
    for path in live_markdown_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith(("docs/brand/", "brand/")):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line) and not _is_legitimate_use(line, forbidden):
                offenders.append(f"{relative}:{number}")
    assert not offenders, (
        f"forbidden public name {forbidden!r} used as the product name on: "
        + ", ".join(offenders[:20])
    )


def test_legitimate_uses_of_forbidden_names_are_not_flagged():
    """Guard the exemptions themselves against becoming a loophole."""
    assert _is_legitimate_use('Use **Chaser Agent** (not "Chase Agent")', "Chase Agent")
    assert _is_legitimate_use("operating under ChaseOS Agent Control Plane", "ChaseOS Agent")
    # A bare product rename is still caught.
    assert not _is_legitimate_use("ChaseOS Agent compiles sources into proposals.", "ChaseOS Agent")


def test_readme_states_the_canonical_relationship_line():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert CANONICAL_NAME in readme
    assert "Runs independently" in readme, (
        "README must carry the canon relationship position; the canon line is "
        "'Runs independently. Works best with ChaseOS.'"
    )


def test_historical_records_are_excluded_from_the_sweep():
    """Guard the exclusion itself, so a later change cannot silently widen it."""
    assert _is_historical(Path("logs/build/2026-08-12-tool-capability-boundary.md"))
    assert _is_historical(Path("07_LOGS/Daily/2026-08-18.md"))
    assert not _is_historical(Path("docs/01_Product/Chaser-Agent-Roadmap.md"))
    assert not _is_historical(Path("README.md"))
