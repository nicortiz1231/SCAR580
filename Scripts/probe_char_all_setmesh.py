"""Search ALL character graphs for SetStaticMesh and ScopeSightMesh."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_all_setmesh.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if not any(k in title for k in ("SetStaticMesh", "ScopeSight", "OpticSightMesh", "SpawnAttachment")):
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("NewMesh", "self", "then", "execute"):
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if linked or val:
                    lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
