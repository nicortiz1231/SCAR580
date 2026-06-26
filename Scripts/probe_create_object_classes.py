"""Read Construct Object class defaults in BeginSetup and LOADSAVE."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_create_object_classes.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_class().get_name() != "K2Node_GenericCreateObject":
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            try:
                default = pin.get_default_as_string()
                if default:
                    lines.append(f"  {pname} default={default!r}")
            except Exception:
                pass
        # downstream slot set
        then = node.find_then_pin()
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            owner = lp.get_owning_node()
            lines.append(f"  then -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

# EventGraph set primary/secondary
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
for name in ("K2Node_VariableSet_20", "K2Node_VariableSet_21", "K2Node_SwitchEnum_0"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{pname}")
            try:
                d = pin.get_default_as_string()
                if d:
                    lines.append(f"  {pname} default={d!r} links={linked}")
                elif linked:
                    lines.append(f"  {pname} -> {linked}")
            except Exception:
                if linked:
                    lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
