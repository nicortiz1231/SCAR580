"""Read LOADSAVE and map spawn weapon construct attachment defaults."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_loadsave_attach.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() not in ("LOADSAVE", "BeginSetup", "EventGraph"):
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_GenericCreateObject":
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if any(k in pname for k in ("WeaponData", "Attachments", "Ammo")):
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                lines.append(f"  {pname}={val!r}")

# Character spawn pickup chain - VariableSet_20 primary
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
for node in editor.list_all_nodes():
    if node.get_name() not in ("K2Node_VariableSet_20", "K2Node_VariableSet_21"):
        continue
    lines.append(f"=== {node.get_name()} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(owner.get_name())
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                linked.append(val)
        except Exception:
            pass
        if linked:
            lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
