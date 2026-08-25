import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRAND_ROOT = ROOT / "brand" / "chaser-agent"
MANIFEST_PATH = BRAND_ROOT / "manifests" / "chaser-agent_canon-core_v1.0.0-rc.1.json"
SOURCE_SHA256 = "ba2872e369b191592434ec702176b562af9f69f1e99b08aadac445faaa8d4608"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _png_dimensions(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    assert payload[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", payload[16:24])


def test_release_candidate_boundaries_are_explicit() -> None:
    manifest = _manifest()
    assert manifest["canon_id"] == "chaser-agent"
    assert manifest["canon_version"] == "1.0.0"
    assert manifest["asset_release_version"] == "1.0.0-rc.1"
    assert manifest["model_version"] == "v0.37.0"
    assert manifest["source_model"]["operator_visual_approved"] is True
    assert manifest["source_model"]["sha256"] == SOURCE_SHA256
    assert manifest["public_media_policy"] == {
        "clean_camera_renders_only": True,
        "blender_viewport_ui_public_use": False,
        "xyz_gizmo_public_use": False,
        "recordly_product_capture": "deferred-separate-pass",
    }
    assert not any(manifest["boundaries"].values())


def test_manifest_assets_exist_and_match_hashes() -> None:
    assets = _manifest()["assets"]
    assert assets
    for asset in assets:
        path = ROOT / asset["path"]
        payload = path.read_bytes()
        assert len(payload) == asset["bytes"], asset["path"]
        assert hashlib.sha256(payload).hexdigest() == asset["sha256"], asset["path"]
        if path.suffix.lower() == ".png":
            assert _png_dimensions(path) == (asset["width"], asset["height"])


def test_required_media_contract_is_complete() -> None:
    manifest = _manifest()
    assets = {asset["path"]: asset for asset in manifest["assets"]}
    prefix = "brand/chaser-agent/exports/canon-core/v1.0.0-rc.1"
    required = {
        f"{prefix}/masters/chaser-agent_neutral-front_transparent_1800x2400.png": (1800, 2400),
        f"{prefix}/masters/chaser-agent_head-shoulders_transparent_2048x2048.png": (2048, 2048),
        f"{prefix}/web/chaser-agent_web-hero_studio-dark_1920x1080.png": (1920, 1080),
        f"{prefix}/model-sheet/chaser-agent_model-sheet_operator-approved_4096x3072.png": (4096, 3072),
        f"{prefix}/turntable/chaser-agent_turntable-studio_720x720_h264.mp4": (720, 720),
        f"{prefix}/turntable/chaser-agent_turntable-studio_720x720_vp9.webm": (720, 720),
    }
    for path, dimensions in required.items():
        assert path in assets
        assert (assets[path]["width"], assets[path]["height"]) == dimensions

    frames = [asset for asset in assets.values() if asset["role"] == "turntable-frame"]
    assert len(frames) == 48
    glb = ROOT / f"{prefix}/interoperability/chaser-agent_model_operator-approved_v0.37.0.glb"
    assert glb.read_bytes()[:4] == b"glTF"
