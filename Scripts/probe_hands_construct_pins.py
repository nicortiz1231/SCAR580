"""Dump all pin values on BeginSetup weapon construct nodes."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_hands_construct_pins.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_GenericCreateObject":
            continue
        lines.append(f"=== {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            except Exception as exc:
                val = f"ERR {exc}"
            if val:
                lines.append(f"  {pname}={val!r}")

# Sniper pickup CDO weapon data defaults
pickup = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"
)
if pickup:
    cdo = unreal.get_default_object(pickup.generated_class())
    lines.append("=== BP_Weapon_Pickup_Sniper CDO ===")
    for prop in sorted(dir(cdo)):
        if prop.startswith("_"):
            continue
        lower = prop.lower()
        if any(k in lower for k in ("item", "ammo", "weapon", "attach")):
            try:
                val = cdo.get_editor_property(prop)
                if val is not None and val != "" and val is not False:
                    if hasattr(val, "get_path_name"):
                        lines.append(f"  {prop}={val.get_path_name()}")
                    else:
                        lines.append(f"  {prop}={val!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
