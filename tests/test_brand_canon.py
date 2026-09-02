import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANON_DIR = ROOT / "docs" / "brand" / "chaser-agent"
MANIFEST_PATH = CANON_DIR / "CHASER-AGENT-CANON-SYNC-MANIFEST.json"
REFERENCE_PATH = (
    ROOT
    / "brand"
    / "chaser-agent"
    / "reference"
    / "selected-base"
    / "chaser-agent_canonical-base-mascot_selected-v1_20260817.png"
)


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_canon_documents_and_version_are_installed() -> None:
    required = {
        "CHASER-AGENT-CHARACTER-CANON-AND-VISUAL-SPEC.md",
        "CHASER-AGENT-FULL-ASSET-ROADMAP-AND-PRODUCTION-SPEC.md",
        "CHASER-AGENT-REPOSITORY-CANON-HANDOVER.md",
        "CHASER-AGENT-CANON-SYNC-MANIFEST.json",
    }
    assert required <= {path.name for path in CANON_DIR.iterdir()}
    manifest = _manifest()
    assert manifest["canon_id"] == "chaser-agent"
    assert manifest["canon_version"] == "1.0.0"
    assert manifest["asset_release_version"] is None
    assert manifest["public_name"] == "Chaser Agent"
    assert manifest["relationship_to_chaseos"] == "runs-independently-works-best-with-chaseos"


def test_selected_reference_matches_locked_hash_and_dimensions() -> None:
    manifest = _manifest()
    payload = REFERENCE_PATH.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == manifest["selected_reference"]["sha256"]
    assert payload[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", payload[16:24])
    assert (width, height) == (
        manifest["selected_reference"]["width"],
        manifest["selected_reference"]["height"],
    )


def test_written_canon_overrides_generated_sheet_copy() -> None:
    canon = (CANON_DIR / "CHASER-AGENT-CHARACTER-CANON-AND-VISUAL-SPEC.md").read_text(
        encoding="utf-8"
    )
    assert "this written canon wins" in canon
    assert "Runs independently. Works best with ChaseOS." in canon
    assert "Permanent or widened authority requires explicit operator confirmation." in canon
