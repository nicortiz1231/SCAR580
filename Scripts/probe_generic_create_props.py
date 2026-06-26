"""Dump all editor properties on BeginSetup GenericCreateObject nodes."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_generic_create_props.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_GenericCreateObject":
            continue
        lines.append(f"=== {node.get_name()} ===")
        for prop in dir(node):
            if prop.startswith("_"):
                continue
            try:
                val = node.get_editor_property(prop)
                if val is not None and val != "" and val is not False:
                    if hasattr(val, "get_path_name"):
                        lines.append(f"  {prop}={val.get_path_name()}")
                    else:
                        lines.append(f"  {prop}={val!r}")
            except Exception:
                pass
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            try:
                default = pin.get_default_as_string()
                if default:
                    lines.append(f"  pin {pname} default={default!r}")
            except Exception:
                pass
            try:
                obj = pin.get_default_object()
                if obj:
                    lines.append(f"  pin {pname} default_object={obj.get_path_name()}")
            except Exception:
                pass

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_EmptyHands.BP_Weapon_EmptyHands",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    cls = unreal.load_class(None, path)
    lines.append(f"CLASS {path} -> {cls.get_path_name() if cls else None}")

OUT.write_text("\n".join(lines))
