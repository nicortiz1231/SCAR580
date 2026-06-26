import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_hands_slot_pins.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        lines.append(f"=== {node.get_name()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if any(k in pname for k in ("Attach", "Ammo", "Weapon", "Sight", "ItemData")):
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                except Exception:
                    val = "?"
                lines.append(f"  {pname} = {val!r}")

# SpawnAttachments fn path from template node
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_CallFunction_46":
        continue
    lines.append(f"template node class={node.get_class().get_name()}")
    try:
        lines.append(f"  member_parent={node.get_editor_property('member_parent')}")
        lines.append(f"  member_name={node.get_editor_property('member_name')}")
    except Exception as exc:
        lines.append(f"  props ERR {exc}")

OUT.write_text("\n".join(lines))
