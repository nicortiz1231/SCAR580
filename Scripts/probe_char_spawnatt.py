"""Trace character SpawnAttachments calls."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_spawnatt.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SpawnAttachments" in title:
        lines.append(f"=== {node.get_name()} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{pname}")
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    linked.append(f"val={val!r}")
            except Exception:
                pass
            if linked:
                lines.append(f"  {pname} -> {linked}")

# walk back to SpawnAttachments from CallFunction_46
for start in ("K2Node_CallFunction_46", "K2Node_CallFunction_138"):
    for node in editor.list_all_nodes():
        if node.get_name() != start:
            continue
        lines.append(f"=== backchain {start} ===")
        stack = [(node.find_input_pin("execute"), 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 10:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                lines.append(f"{'  '*depth}{owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")
                for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                    if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_INPUT:
                        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                        if pn == "execute":
                            stack.append((p, depth + 1))

OUT.write_text("\n".join(lines))
