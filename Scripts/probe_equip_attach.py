import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_equip_attach.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "Equip":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== Equip graph ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Attach", "Sight", "Scope", "Item", "SetAmmo", "Spawn", "Break")):
            lines.append(f"  {node.get_name()} | {title}")

# SetAmmo call sites on character - what pins are wired
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if title != "SetAmmo" and "SetAmmo" not in title:
        continue
    lines.append(f"=== {node.get_name()} | {title} ===")
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
        if linked:
            lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
