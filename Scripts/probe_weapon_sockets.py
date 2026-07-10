import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_sockets.log")
lines = []

def log(msg):
    lines.append(msg)

CAMERA_MESH = "/Game/BodycamFPSKIT/Blueprints/Camera/SKM_Camera.SKM_Camera"
MANNY_MESH = "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Meshes/SKM_Manny.SKM_Manny"

for label, path in (("camera", CAMERA_MESH), ("manny", MANNY_MESH)):
    mesh = unreal.load_asset(path)
    skel = mesh.get_editor_property("skeleton") if mesh else None
    log(f"=== {label} skeleton sockets ===")
    if skel:
        for sock in skel.get_socket_names():
            s = str(sock)
            if any(k in s.lower() for k in ("hand", "gun", "ik", "weapon")):
                log(f"  {s}")

OUT.write_text("\n".join(lines))
