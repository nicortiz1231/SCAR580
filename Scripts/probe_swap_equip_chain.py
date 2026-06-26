"""Trace SwapWeapon to Equip and SpawnAttachments."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_swap_equip_chain.log")
lines = []


def walk_exec(editor, start_name: str, depth=0, max_depth=20):
    for node in editor.list_all_nodes():
        if node.get_name() != start_name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{'  '*depth}{start_name} | {title}")
        pins = []
        if hasattr(node, "find_then_pin"):
            t = node.find_then_pin()
            if t:
                pins.append(t)
        if node.get_class().get_name() == "K2Node_IfThenElse":
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("then", "else"):
                    pins.append(pin)
        for pin in pins:
            if depth >= max_depth:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                walk_exec(editor, owner.get_name(), depth + 1, max_depth)
        return


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

lines.append("=== SwapWeapon ===")
walk_exec(editor, "K2Node_CustomEvent_13")

lines.append("=== CallFunction_136 SwapWeapon ===")
walk_exec(editor, "K2Node_CallFunction_136")

lines.append("=== Equip ===")
walk_exec(editor, "K2Node_CallFunction_17")

OUT.write_text("\n".join(lines))
