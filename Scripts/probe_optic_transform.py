"""Compare OpticSight transform: SCAR vs original Bodycam kit."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_optic_transform.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
sniper_bp = unreal.load_asset(SNIPER)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "OpticSight" not in obj.get_name():
        continue
    sm = obj.get_editor_property("static_mesh")
    lines.append(f"OpticSight mesh={sm.get_name() if sm else None}")
    for prop in ("relative_location", "relative_rotation", "relative_scale3d"):
        lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(char)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for node in editor.list_all_nodes():
    title = str(node.get_node_title())
    if "SetNearClipPlane" in title:
        lines.append(f"char has {node.get_name()} | {title.replace(chr(10),' | ')}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                lines.append(f"  {unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}={val}")

# Recoil struct from DT
sniper_cdo = unreal.get_default_object(sniper_bp.generated_class())
pv = sniper_cdo.get_editor_property("ProceduralValues")
for block in ("WeaponValues", "RecoilValues"):
    st = pv.get_editor_property(block)
    lines.append(f"=== {block} ===")
    for prop in sorted(dir(st)):
        if prop.startswith("_"):
            continue
        try:
            v = st.get_editor_property(prop)
            if hasattr(v, "x"):
                lines.append(f"  {prop}=({v.x:.3f},{v.y:.3f},{v.z:.3f})")
            else:
                lines.append(f"  {prop}={v!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
