import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_recoil_graph.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() not in ("Recoil", "EventGraph"):
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {g.get_name()} ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Recoil", "Procedural", "Kick", "Camera", "Clip")):
            lines.append(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if "Recoil" in pn or pn in ("execute", "then", "self"):
                    linked = []
                    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                        linked.append(lp.get_owning_node().get_name())
                    if linked:
                        lines.append(f"    {pn} -> {linked}")
OUT.write_text("\n".join(lines))
