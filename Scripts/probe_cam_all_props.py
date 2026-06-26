import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_cam_all_props.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"=== {obj.get_name()} ===")
    for prop in sorted(dir(obj)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if not any(k in lower for k in ("clip", "near", "custom")):
            continue
        try:
            lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
pv = unreal.get_default_object(sniper.generated_class()).get_editor_property("ProceduralValues")
for block in ("WeaponValues", "RecoilValues"):
    try:
        st = pv.get_editor_property(block)
        lines.append(f"=== {block} ===")
        for prop in sorted(dir(st)):
            if prop.startswith("_"):
                continue
            try:
                lines.append(f"  {prop}={st.get_editor_property(prop)!r}")
            except Exception:
                pass
    except Exception as exc:
        lines.append(f"{block} ERR {exc}")
OUT.write_text("\n".join(lines))
