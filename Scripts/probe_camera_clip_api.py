"""Find blueprint-callable camera near clip APIs in UE 5.8."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_camera_clip_api.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for fn_path in (
    "/Script/Engine.CameraComponent:SetNearClipPlane",
    "/Script/Engine.CameraComponent:SetOrthoNearClipPlane",
    "/Script/Engine.KismetSystemLibrary:ExecuteConsoleCommand",
    "/Script/Engine.PlayerCameraManager:UpdateCamera",
):
    node = editor.add_call_function_node(fn_path)
    lines.append(f"spawn {fn_path} -> {node!r}")

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
pv = unreal.get_default_object(sniper.generated_class()).get_editor_property("ProceduralValues")
wv = pv.get_editor_property("WeaponValues")
for prop in (
    "BasePoseLoc", "BasePoseRot", "AimPoseLoc", "AimPoseRot", "AimLoc", "AimRot",
    "SprintPoseLoc", "IdlePoseLoc", "WallPoseLoc",
):
    try:
        v = wv.get_editor_property(prop)
        if hasattr(v, "x"):
            lines.append(f"WeaponValues.{prop}=({v.x:.3f},{v.y:.3f},{v.z:.3f})")
        else:
            lines.append(f"WeaponValues.{prop}={v!r}")
    except Exception as exc:
        lines.append(f"WeaponValues.{prop} ERR {exc}")

rv = pv.get_editor_property("RecoilValues")
for prop in ("RecoilLoc", "RecoilRot", "RecoilTranslation", "RecoilRotation", "Kickback"):
    try:
        v = rv.get_editor_property(prop)
        if hasattr(v, "x"):
            lines.append(f"RecoilValues.{prop}=({v.x:.3f},{v.y:.3f},{v.z:.3f})")
    except Exception as exc:
        lines.append(f"RecoilValues.{prop} ERR {exc}")

OUT.write_text("\n".join(lines))
