"""Dump sniper DT row fields via struct asset."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_struct_fields.log")
lines = []

dt = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/DT_SniperAnimationValues.DT_SniperAnimationValues"
)
lines.append(f"DT={dt}")

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
pv = unreal.get_default_object(sniper.generated_class()).get_editor_property("ProceduralValues")
lines.append(f"ProceduralValues={pv}")

for struct_path in (
    "/Game/BodycamFPSKIT/Blueprints/Structs/ST_ProceduralWeaponValues.ST_ProceduralWeaponValues",
    "/Game/BodycamFPSKIT/Blueprints/Structs/ST_RecoilValues.ST_RecoilValues",
):
    st = unreal.load_asset(struct_path)
    lines.append(f"=== struct {struct_path.split('/')[-1]} ===")
    if st:
        try:
            for field in unreal.UserDefinedStructEditorLibrary.get_all_structure_fields(st):
                lines.append(f"  field={field}")
        except Exception as exc:
            lines.append(f"  get_all_structure_fields ERR {exc}")
        try:
            names = st.get_structure_field_names()
            lines.append(f"  names={list(names)}")
        except Exception as exc:
            lines.append(f"  get_structure_field_names ERR {exc}")

for block_name in ("WeaponValues", "RecoilValues"):
    try:
        block = pv.get_editor_property(block_name)
        lines.append(f"=== {block_name} type={type(block)} ===")
        for prop in (
            "BasePoseLoc", "BasePoseRot", "SprintPoseLoc", "SprintPoseRot",
            "CrouchPoseLoc", "CrouchPoseRot", "LeanPoseLoc", "LeanPoseRot",
            "Loc", "Rot", "Translation", "Rotation", "Kick", "Kickback",
            "Recoil", "Pushback", "Backward", "Forward",
        ):
            try:
                v = block.get_editor_property(prop)
                if hasattr(v, "x"):
                    lines.append(f"  {prop}=({v.x:.4f},{v.y:.4f},{v.z:.4f})")
                elif hasattr(v, "pitch"):
                    lines.append(f"  {prop}=(p{v.pitch:.2f},y{v.yaw:.2f},r{v.roll:.2f})")
                else:
                    lines.append(f"  {prop}={v!r}")
            except Exception:
                pass
    except Exception as exc:
        lines.append(f"{block_name} ERR {exc}")

OUT.write_text("\n".join(lines))
