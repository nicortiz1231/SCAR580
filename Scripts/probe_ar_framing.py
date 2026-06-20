"""Probe BP_FPCharacter camera/weapon component transforms for AR framing."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_framing.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
bp = unreal.load_asset(BP)
cdo = unreal.get_default_object(bp.generated_class())

p(f"BODYCAM={cdo.get_editor_property('BODYCAM')}")
p(f"FOV_Base={cdo.get_editor_property('FOV_Base')}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
seen = set()
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    oid = id(obj)
    if oid in seen:
        continue
    seen.add(oid)

    name = obj.get_name()
    if not any(token in name for token in ("SpringArm", "FirstPersonCamera", "WeaponSpawn")):
        continue

    p(f"=== {name} ({obj.get_class().get_name()}) ===")
    for prop in (
        "relative_location",
        "RelativeLocation",
        "relative_rotation",
        "RelativeRotation",
        "relative_scale3d",
        "RelativeScale3D",
        "target_arm_length",
        "TargetArmLength",
        "socket_offset",
        "SocketOffset",
        "target_offset",
        "TargetOffset",
        "field_of_view",
        "FieldOfView",
        "use_pawn_control_rotation",
        "bUsePawnControlRotation",
        "inherit_pitch",
        "bInheritPitch",
        "inherit_yaw",
        "bInheritYaw",
        "inherit_roll",
        "bInheritRoll",
    ):
        try:
            p(f"  {prop}={obj.get_editor_property(prop)}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
