"""Find character SetStaticMesh + ScopeSightMesh in ALL graphs."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_scope_all.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        t = str(node.get_node_title()).replace("\n", " | ")
        if not any(k in t for k in ("SetStaticMesh", "ScopeSight", "OpticSight", "SetVisibility")):
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()} | {t}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self", "NewMesh"):
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if linked or val:
                    lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
