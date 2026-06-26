"""Probe BP_FPCharacter bullet casing and tracer chain end."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_impact_fx5.log")


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def walk(node, hops=15):
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

    # tracer chain
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
    graph = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "Fire_HitScan")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    n19 = next(n for n in editor.list_all_nodes() if n.get_name() == "K2Node_CallFunction_19")
    log("tracer chain:")
    walk(n19)

    n11 = next(n for n in editor.list_all_nodes() if n.get_name() == "K2Node_CallFunction_11")
    log("after niagara 11:")
    walk(n11)

    # character bullet casing
    bp2 = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp2):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            t = title(node)
            if "BulletCasing" in t or "Bullet Casing" in t or node.get_name() == "K2Node_SpawnActorFromClass_0":
                log(f"CHAR {graph.get_name()} {node.get_name()} | {t}")
                walk(node, 8)

    log("done")


main()
