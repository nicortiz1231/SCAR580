"""Fully lock FPS arms to camera rotation (zero camera-look sway), while
restoring movement-based sway back to its original value (that part was
never the source of AR jitter). "Fixed to the camera" means the arms/weapon
should move exactly with the camera with no independent spring lag from
look/camera rotation changes.
"""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_arm_lock_to_camera.log")

ORIGINAL_MOVE_SWAY = unreal.Vector(0.6, -0.6, 0.0)
ZERO = unreal.Vector(0.0, 0.0, 0.0)


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(f"[fix_ar_arm_lock_to_camera] {msg}")


def get_prop(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception as exc:
        return f"ERR {exc}"


def set_prop(obj, name, value) -> bool:
    try:
        obj.set_editor_property(name, value)
        log(f"Set {obj.get_name()}.{name} = {value}")
        return True
    except Exception as exc:
        log(f"FAILED {obj.get_name()}.{name} = {value}: {exc}")
        return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    subobjs = []
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if obj:
            subobjs.append(obj)

    def find(name_token):
        for o in subobjs:
            if name_token in o.get_name():
                return o
        return None

    proc_anim = find("ProceduralAnimation")
    if not proc_anim:
        raise RuntimeError("AC_ProceduralAnimation not found on BP_FPCharacter")

    log(f"before MouseSwayAmplitude = {get_prop(proc_anim, 'MouseSwayAmplitude')}")
    log(f"before MoveSwayAmplitude = {get_prop(proc_anim, 'MoveSwayAmplitude')}")

    # Zero camera-look sway entirely -> arms rigidly track camera/aim rotation.
    set_prop(proc_anim, "MouseSwayAmplitude", ZERO)
    # Restore movement sway to its original value (unrelated to AR jitter).
    set_prop(proc_anim, "MoveSwayAmplitude", ORIGINAL_MOVE_SWAY)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Compiled and saved BP_FPCharacter")


main()
