"""Check what the FPS arms/weapon mesh and camera are actually attached to,
and how the arms' rotation is driven (ControlRotation vs camera transform)."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_arms_attachment.log")


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(f"[probe_arms_attachment] {msg}")


if LOG_PATH.exists():
    LOG_PATH.unlink()

bp = unreal.load_asset(BP_ASSET)
if not bp:
    raise RuntimeError(f"Missing {BP_ASSET}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
seen = set()

for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or id(obj) in seen:
        continue
    seen.add(id(obj))
    name = obj.get_name()
    class_name = obj.get_class().get_name()

    parent_name = "N/A (not SceneComponent)"
    socket = "N/A"
    if isinstance(obj, unreal.SceneComponent):
        try:
            parent = obj.get_attach_parent()
            parent_name = parent.get_name() if parent else "None"
        except Exception as exc:
            parent_name = f"ERR {exc}"
        try:
            socket = str(obj.get_attach_socket_name())
        except Exception as exc:
            socket = f"ERR {exc}"

    mesh_asset = None
    if isinstance(obj, unreal.SkeletalMeshComponent):
        try:
            sk = obj.get_editor_property("skeletal_mesh_asset")
        except Exception:
            try:
                sk = obj.get_editor_property("skeletal_mesh")
            except Exception:
                sk = None
        mesh_asset = sk.get_path_name() if sk else None

    log(f"{name} ({class_name}) parent={parent_name} socket={socket} mesh={mesh_asset}")

log("DONE")
