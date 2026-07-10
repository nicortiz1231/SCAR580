import unreal
import traceback
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fp_opponent_visual.log")
OUT.write_text("")

def log(msg):
    with OUT.open("a") as f:
        f.write(msg + "\n")

def dump_graph(gname):
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != gname:
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        log(f"=== {gname} ({len(ed.list_all_nodes())} nodes) ===")
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            log(f"  {node.get_name()} | {title}")

try:
    for gname in ("ConstructionScript", "UserConstructionScript", "SpawnMesh", "SetupMesh", "CreateMesh"):
        dump_graph(gname)

    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    log("=== All graph names ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        log(f"  {g.get_name()}")

    # Follow BeginPlay exec chain first 15 nodes
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != "EventGraph":
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        begin = next((n for n in ed.list_all_nodes() if str(n.get_node_title()).startswith("Event BeginPlay")), None)
        if not begin:
            continue
        log("=== BeginPlay chain ===")
        node = begin
        for _ in range(25):
            log(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
            then = node.find_output_pin("then")
            if not then:
                break
            links = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
            if not links:
                break
            node = links[0].get_owning_node()

    log("done")
except Exception:
    log(traceback.format_exc())
