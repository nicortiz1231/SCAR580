"""Probe impact decal chain after SpawnDecalAttached."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_decal_chain.log")
BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def walk(node, hops=12):
    cur = node
    for i in range(hops):
        log(f"  {i}: {cur.get_name()} | {title(cur)}")
        then = cur.find_output_pin("then")
        if not then:
            break
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
        if not links:
            log("    end")
            break
        cur = unreal.BlueprintGraphPinLibrary.get_owning_node(links[0])


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP)
    graph = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "Fire_HitScan")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    cast1 = next(n for n in editor.list_all_nodes() if n.get_name() == "K2Node_DynamicCast_1")
    log("from DynamicCast_1 then:")
    walk(cast1)

    m0 = next((n for n in editor.list_all_nodes() if n.get_name() == "K2Node_MacroInstance_0"), None)
    if m0:
        log("from MacroInstance_0 then:")
        walk(m0)

    log("done")


main()
