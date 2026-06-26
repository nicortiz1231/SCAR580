"""Trace end of impact concrete niagara exec chain."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_impact_fx4.log")
BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def walk_exec_from(node, max_hops=20):
    cur = node
    for i in range(max_hops):
        log(f"  {i}: {cur.get_name()} | {title(cur)}")
        then = cur.find_output_pin("then")
        if not then:
            break
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
        if not links:
            log("    (end)")
            break
        cur = unreal.BlueprintGraphPinLibrary.get_owning_node(links[0])


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP)
    graph = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "Fire_HitScan")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    seq = next(n for n in editor.list_all_nodes() if n.get_name() == "K2Node_ExecutionSequence_2")
    for pin in seq.get_pins():
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not name.startswith("then_"):
            continue
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
        if not links:
            log(f"seq {name}: unused")
            continue
        first = unreal.BlueprintGraphPinLibrary.get_owning_node(links[0])
        log(f"seq {name} -> {first.get_name()} | {title(first)}")
        walk_exec_from(first)

    cast1 = next(n for n in editor.list_all_nodes() if n.get_name() == "K2Node_DynamicCast_1")
    log("=== DynamicCast_1 branches ===")
    for pin_name in ("then", "CastFailed"):
        pin = cast1.find_output_pin(pin_name)
        if not pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  {pin_name} -> {n.get_name() if n else '?'}")

    log("done")


main()
