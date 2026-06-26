import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo2.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "SetWeaponAmmoData":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    entry = None
    for node in editor.list_all_nodes():
        if node.get_class().get_name() == "K2Node_FunctionEntry":
            entry = node
            break
    lines.append("=== SetWeaponAmmoData chain ===")
    stack = [(entry.find_pin("then"), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 30:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            t = str(owner.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{owner.get_name()} | {t}")
            nxt = owner.find_then_pin()
            if nxt:
                stack.append((nxt, depth + 1))

OUT.write_text("\n".join(lines))
