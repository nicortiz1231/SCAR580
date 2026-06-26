import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_spawn.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_SpawnActorFromClass_2":
        continue
    lines.append(f"=== {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}:{pname}")
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                linked.append(val)
        except Exception:
            pass
        lines.append(f"  {pname} -> {linked}")

    # exec chain forward
    then = node.find_then_pin()
    stack = [(then, 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 15:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
            nxt = o.find_then_pin()
            if nxt:
                stack.append((nxt, depth + 1))

    # exec chain backward
    lines.append("=== backchain ===")
    stack = [(node.find_input_pin("execute"), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 15:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
