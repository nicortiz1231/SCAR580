"""Trace Is Valid branches after swap spawn."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_isvalid_branches.log")
lines = []


def walk_from_pin(editor, pin, depth=0, max_depth=25, label=""):
    if not pin or depth > max_depth:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = lp.get_owning_node()
        title = str(owner.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}[{label}] {owner.get_name()} | {title}")
        pins = []
        if hasattr(owner, "find_then_pin"):
            t = owner.find_then_pin()
            if t:
                pins.append(("then", t))
        if owner.get_class().get_name() == "K2Node_IfThenElse":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn in ("then", "else"):
                    pins.append((pn, p))
        if owner.get_class().get_name() == "K2Node_MacroInstance":
            for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pn in ("Is Valid", "Is Not Valid"):
                    walk_from_pin(editor, p, depth + 1, max_depth, pn)
        for pn, p in pins:
            walk_from_pin(editor, p, depth + 1, max_depth, pn)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_MacroInstance_4":
        continue
    lines.append("=== MacroInstance_4 branches ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn in ("Is Valid", "Is Not Valid"):
            walk_from_pin(editor, pin, 0, 25, pn)

OUT.write_text("\n".join(lines))
