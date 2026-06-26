import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_equip_fn.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "Equip":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    entry = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_FunctionEntry":
            entry = node
            break
    lines.append("=== Equip exec chain ===")
    stack = [(entry.find_pin("then"), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 40:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            t = str(o.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{o.get_name()} | {t}")
            nxt = o.find_then_pin()
            if nxt:
                stack.append((nxt, depth + 1))
            if o.get_class().get_name() == "K2Node_IfThenElse":
                for p in unreal.BlueprintEditorLibrary.list_all_pins(o):
                    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                    if pn == "else":
                        for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                            o2 = lp2.get_owning_node()
                            lines.append(f"{'  '*(depth+1)}[else] {o2.get_name()} | {str(o2.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
