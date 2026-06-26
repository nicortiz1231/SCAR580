import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_exec_chains.log")
lines = []

def dump_exec(editor, start_node, label, depth=0):
    lines.append(f"=== {label} ===")
    stack = [(start_node.find_output_pin("then") if hasattr(start_node,'find_output_pin') else start_node.find_pin("then"), 0)]
    if start_node.get_class().get_name() == "K2Node_Event":
        stack = [(start_node.find_pin("then"), 0)]
    while stack:
        pin, d = stack.pop()
        if not pin or d > 12:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            t = str(o.get_node_title()).replace("\n"," | ")
            lines.append(f"{'  '*d}{o.get_name()} | {t}")
            nxt = o.find_output_pin("then") if hasattr(o,'find_output_pin') else None
            if nxt:
                stack.append((nxt, d+1))

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
for gname in ("EventGraph", "UserConstructionScript"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(sniper):
        if g.get_name() != gname:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            if node.get_class().get_name() == "K2Node_Event" and "SpawnAttachments" in str(node.get_node_title()):
                dump_exec(editor, node, f"sniper {gname} SpawnAttachments")
            if node.get_class().get_name() == "K2Node_Event" and "BeginPlay" in str(node.get_node_title()):
                dump_exec(editor, node, f"sniper {gname} BeginPlay")
            if node.get_class().get_name() == "K2Node_CallParentFunction" and gname=="UserConstructionScript":
                dump_exec(editor, node, f"sniper UCS parent")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for name in ("K2Node_CallFunction_140", "K2Node_CallFunction_141"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        dump_exec(editor, node, f"char after {name}")
OUT.write_text("\n".join(lines))
