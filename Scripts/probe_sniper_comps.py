import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_comps.log")
lines = []

sniper_bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if obj:
        lines.append(f"{obj.get_name()} | {obj.get_class().get_name()}")
        if obj.get_class().get_name() == "StaticMeshComponent":
            try:
                sm = obj.get_editor_property("static_mesh")
                lines.append(f"  static_mesh={sm.get_name() if sm else None}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
