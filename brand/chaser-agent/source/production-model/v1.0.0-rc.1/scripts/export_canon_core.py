from __future__ import annotations

import hashlib
import os
from pathlib import Path

import bpy
from mathutils import Vector


MODEL_DIR = Path(__file__).resolve().parents[1]
BRAND_DIR = MODEL_DIR.parents[2]
EXPORT_DIR = BRAND_DIR / "exports" / "canon-core" / "v1.0.0-rc.1"
QA_DIR = BRAND_DIR / "qa" / "v1.0.0-rc.1" / "render-drafts"
MODEL_PATH = MODEL_DIR / "chaser-agent_production-model_operator-approved_v0.37.0_20260824.blend"
EXPECTED_SOURCE_SHA256 = "ba2872e369b191592434ec702176b562af9f69f1e99b08aadac445faaa8d4608"


def ensure_approved_source() -> bpy.types.Object:
    digest = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Approved source hash mismatch: {digest}")
    root = bpy.data.objects.get("CHASER_AGENT_BLOCKOUT_ROOT")
    if root is None:
        raise RuntimeError("Missing approved Chaser Agent root")
    if "OPERATOR VISUAL APPROVED" not in str(root.get("status", "")):
        raise RuntimeError(f"Source is not operator-approved: {root.get('status')}")
    return root


def look_at(camera: bpy.types.Object, target: tuple[float, float, float]) -> None:
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def camera_copy(name: str, source_name: str, location=None, target=None, lens=None, shift_x=0.0):
    source = bpy.data.objects[source_name]
    camera = source.copy()
    camera.data = source.data.copy()
    camera.name = name
    camera.data.name = f"{name}_data"
    bpy.context.collection.objects.link(camera)
    if location is not None:
        camera.location = location
    if target is not None:
        look_at(camera, target)
    if lens is not None:
        camera.data.lens = lens
    camera.data.sensor_fit = "VERTICAL"
    camera.data.shift_x = shift_x
    return camera


def configure_output(width: int, height: int, transparent: bool) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 30


def floor_visible(visible: bool) -> None:
    floor = bpy.data.objects.get("QA_floor")
    if floor is not None:
        floor.hide_render = not visible


def world_ink(enabled: bool) -> None:
    world = bpy.context.scene.world
    if world is None or not world.use_nodes:
        return
    background = world.node_tree.nodes.get("Background")
    if background is None:
        return
    if enabled:
        background.inputs["Color"].default_value = (0.0018, 0.0030, 0.0065, 1.0)
        background.inputs["Strength"].default_value = 0.16


def render(camera, path: Path, width: int, height: int, transparent: bool, floor: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    configure_output(width, height, transparent)
    floor_visible(floor)
    world_ink(not transparent and floor)
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.camera = camera
    scene.view_layers[0].material_override = None
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED={path}|{width}x{height}|transparent={transparent}")


def silhouette_material(name: str, rgba: tuple[float, float, float, float]):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = rgba
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def render_silhouette(camera, path: Path, material) -> None:
    configure_output(1024, 1536, True)
    floor_visible(False)
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.camera = camera
    scene.view_layers[0].material_override = material
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override = None
    print(f"SILHOUETTE={path}")


def export_glb(root: bpy.types.Object) -> Path:
    output = EXPORT_DIR / "interoperability" / "chaser-agent_model_operator-approved_v0.37.0.glb"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    stack = [root]
    while stack:
        obj = stack.pop()
        obj.select_set(True)
        stack.extend(obj.children)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=True,
        export_cameras=False,
        export_lights=False,
        export_apply=True,
        export_animations=False,
    )
    print(f"GLB_EXPORTED={output}")
    return output


def build_cameras():
    front = bpy.data.objects["Camera_front"]
    three_quarter = bpy.data.objects["Camera_three_quarter"]
    side = bpy.data.objects["Camera_side"]
    back = bpy.data.objects["Camera_back"]
    for camera in (front, three_quarter, side, back):
        camera.data.sensor_fit = "VERTICAL"
        camera.data.lens = 44.0
    head = camera_copy(
        "Camera_canon_head_shoulders",
        "Camera_front",
        location=(0.0, -6.4, 2.78),
        target=(0.0, 0.0, 2.62),
        lens=52.0,
    )
    hero = camera_copy(
        "Camera_canon_web_hero",
        "Camera_three_quarter",
        location=(6.8, -8.6, 2.68),
        target=(0.0, 0.0, 1.48),
        lens=60.0,
        shift_x=-0.22,
    )
    return front, three_quarter, side, back, head, hero


def render_drafts(cameras) -> None:
    front, three_quarter, _side, back, head, hero = cameras
    QA_DIR.mkdir(parents=True, exist_ok=True)
    render(front, QA_DIR / "draft_front-transparent.png", 450, 600, True, False)
    render(three_quarter, QA_DIR / "draft_three-quarter-transparent.png", 450, 600, True, False)
    render(back, QA_DIR / "draft_back-transparent.png", 450, 600, True, False)
    render(head, QA_DIR / "draft_avatar-master.png", 600, 600, True, False)
    render(hero, QA_DIR / "draft_web-hero-studio.png", 960, 540, False, True)


def render_masters(cameras) -> None:
    front, three_quarter, side, back, head, hero = cameras
    masters = EXPORT_DIR / "masters"
    render(front, masters / "chaser-agent_neutral-front_transparent_1800x2400.png", 1800, 2400, True, False)
    render(three_quarter, masters / "chaser-agent_neutral-three-quarter_transparent_1800x2400.png", 1800, 2400, True, False)
    render(side, masters / "chaser-agent_neutral-side_transparent_1800x2400.png", 1800, 2400, True, False)
    render(back, masters / "chaser-agent_neutral-back_transparent_1800x2400.png", 1800, 2400, True, False)
    render(head, masters / "chaser-agent_head-shoulders_transparent_2048x2048.png", 2048, 2048, True, False)
    render(hero, EXPORT_DIR / "web" / "chaser-agent_web-hero_studio-dark_1920x1080.png", 1920, 1080, False, True)
    black = silhouette_material("QA Canon Black Silhouette", (0.007, 0.008, 0.012, 1.0))
    white = silhouette_material("QA Canon White Silhouette", (0.92, 0.93, 0.94, 1.0))
    render_silhouette(front, EXPORT_DIR / "silhouette" / "chaser-agent_silhouette-black_1024x1536.png", black)
    render_silhouette(front, EXPORT_DIR / "silhouette" / "chaser-agent_silhouette-white_1024x1536.png", white)


def render_turntable(root, front) -> None:
    frame_dir = EXPORT_DIR / "turntable" / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    configure_output(720, 720, False)
    floor_visible(True)
    scene = bpy.context.scene
    scene.camera = front
    scene.view_layers[0].material_override = None
    for index in range(48):
        scene.frame_set(1 + index * 2)
        output = frame_dir / f"chaser-agent_turntable_{index:03d}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        print(f"TURNTABLE={index + 1}/48|{output}")
    scene.frame_set(1)
    export_glb(root)


def main() -> None:
    root = ensure_approved_source()
    cameras = build_cameras()
    mode = os.environ.get("CHASER_EXPORT_MODE", "drafts").lower()
    if mode == "drafts":
        render_drafts(cameras)
    elif mode == "framing":
        render(cameras[0], QA_DIR / "draft_front-transparent.png", 450, 600, True, False)
        render(cameras[4], QA_DIR / "draft_avatar-master.png", 600, 600, True, False)
    elif mode == "masters":
        render_masters(cameras)
    elif mode == "silhouette":
        black = silhouette_material("QA Canon Black Silhouette", (0.0021, 0.0030, 0.0065, 1.0))
        white = silhouette_material("QA Canon White Silhouette", (0.92, 0.93, 0.94, 1.0))
        render_silhouette(cameras[0], EXPORT_DIR / "silhouette" / "chaser-agent_silhouette-black_1024x1536.png", black)
        render_silhouette(cameras[0], EXPORT_DIR / "silhouette" / "chaser-agent_silhouette-white_1024x1536.png", white)
    elif mode == "turntable":
        render_turntable(root, cameras[0])
    elif mode == "all":
        render_masters(cameras)
        render_turntable(root, cameras[0])
    else:
        raise RuntimeError(f"Unsupported CHASER_EXPORT_MODE={mode}")
    print(f"EXPORT_MODE_COMPLETE={mode}")


if __name__ == "__main__":
    main()
