"""Trace map pickup spawn attachment application."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_map_spawn_attach.log")
lines = []


def walk(pin, depth=0, max_depth=25):
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
        if owner.get_class().get_name() == "K2Node_SwitchEnum":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn.startswith("NewEnumerator"):
                    pins.append(p)
        for p in pins:
            walk(p, depth + 1, max_depth)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_SpawnActorFromClass_2":
        continue
    lines.append("=== from SpawnActorFromClass_2 ===")
    walk(node.find_then_pin())

OUT.write_text("\n".join(lines))
