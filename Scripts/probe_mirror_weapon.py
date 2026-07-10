import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mirror_weapon.log")
OUT.write_text("")

def log(msg):
    with OUT.open("a") as f:
        f.write(msg + "\n")

BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
bp = unreal.load_asset(BP)

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        cls = node.get_class().get_name()
        title = str(node.get_node_title()).replace("\n", " | ")
        if cls in ("K2Node_AddComponent", "K2Node_AddComponentByClass") or "Skeletal Mesh" in title or "Add Component" in title:
            log(f"[{g.get_name()}] {node.get_name()} | {cls} | {title}")
