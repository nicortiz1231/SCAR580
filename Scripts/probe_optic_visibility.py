"""Probe OpticSight visibility defaults and custom event names."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_optic_visibility.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
sniper_bp = unreal.load_asset(SNIPER)
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))

for node in eg.list_all_nodes():
    if node.get_class().get_name() != "K2Node_CustomEvent":
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"custom event {node.get_name()} title={title}")
    for prop in dir(node):
        if "custom" in prop.lower() or "function" in prop.lower() or "name" in prop.lower():
            if prop.startswith("_"):
                continue
            try:
                val = node.get_editor_property(prop)
                if val:
                    lines.append(f"  {prop}={val!r}")
            except Exception:
                pass

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "OpticSight" not in obj.get_name():
        continue
    lines.append(f"=== {obj.get_name()} ===")
    for prop in sorted(dir(obj)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if not any(k in lower for k in ("visible", "hidden", "mesh", "collision", "attach")):
            continue
        try:
            val = obj.get_editor_property(prop)
            lines.append(f"  {prop}={val!r}")
        except Exception:
            pass

# rifle compare
rifle = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle")
rcdo = unreal.get_default_object(rifle.generated_class())
try:
    ro = rcdo.get_editor_property("OpticSight")
    lines.append(f"rifle OpticSight mesh={ro.get_editor_property('static_mesh')}")
except Exception as exc:
    lines.append(f"rifle ERR {exc}")

OUT.write_text("\n".join(lines))
