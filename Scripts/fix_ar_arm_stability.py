"""Reduce AR-induced FPS arm jitter without touching desktop mouse-look feel.

Root cause: FirstPersonCamera.bLockToHmd now drives raw, unsmoothed ARKit
device orientation straight into the render camera every frame (needed for
free look-around). AC_ProceduralAnimation's mouse-sway spring and
AC_BodycamCamera's shake system both react to frame-to-frame camera rotation
deltas, treating tiny per-frame ARKit sensor noise as if it were fast mouse
movement, which visibly shakes the arms/weapon. We damp that reaction instead
of touching the (now working) camera tracking path.
"""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_ar_arm_stability.log")

# Scale sway/shake amplitude for AR without fully disabling the effect.
SWAY_SCALE = 0.25


def log(msg: str) -> None:
    with LOG_PATH.open("a") as f:
        f.write(str(msg) + "\n")
    unreal.log(f"[fix_ar_arm_stability] {msg}")


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


def scale_vector_like(value, scale):
    if isinstance(value, unreal.Vector):
        return unreal.Vector(value.x * scale, value.y * scale, value.z * scale)
    if isinstance(value, unreal.Rotator):
        return unreal.Rotator(value.pitch * scale, value.yaw * scale, value.roll * scale)
    if isinstance(value, unreal.Vector2D):
        return unreal.Vector2D(value.x * scale, value.y * scale)
    return None


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    cdo = unreal.get_default_object(bp.generated_class())
    comps = cdo.get_components_by_class(unreal.ActorComponent.static_class())

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
    bodycam = find("BodycamCamera")

    if proc_anim:
        log(f"Found {proc_anim.get_name()}")
        for prop_name in ("MouseSwayAmplitude", "MoveSwayAmplitude"):
            current = get_prop(proc_anim, prop_name)
            log(f"  before {prop_name} = {current}")
            scaled = scale_vector_like(current, SWAY_SCALE) if not isinstance(current, str) else None
            if scaled is not None:
                set_prop(proc_anim, prop_name, scaled)
            else:
                log(f"  skip scaling {prop_name} (unrecognized type)")
    else:
        log("AC_ProceduralAnimation not found on BP_FPCharacter")

    if bodycam:
        log(f"Found {bodycam.get_name()}")
        log(f"  before Camera Shake = {get_prop(bodycam, 'Camera Shake')}")
        set_prop(bodycam, "Camera Shake", False)
    else:
        log("AC_BodycamCamera not found on BP_FPCharacter")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Compiled and saved BP_FPCharacter")


main()
