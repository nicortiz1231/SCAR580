"""Continue chain after RefreshUI from weapon swap."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_after_refreshui.log")
lines = []


def walk_from_pin(pin, depth=0, max_depth=30):
    if not pin or depth > max_depth:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = lp.get_owning_node()
        title = str(owner.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}{owner.get_name()} | {title}")
        pins = []
        if hasattr(owner, "find_then_pin"):
            t = owner.find_then_pin()
            if t:
                pins.append(t)
        if owner.get_class().get_name() == "K2Node_IfThenElse":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn in ("then", "else"):
                    pins.append(p)
        for p in pins:
            walk_from_pin(p, depth + 1, max_depth)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_Knot_18":
        continue
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        lines.append("=== After Knot_18 ===")
        walk_from_pin(pin)

OUT.write_text("\n".join(lines))
