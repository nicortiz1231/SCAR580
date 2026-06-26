"""Map DynamicCast_1 and impact decal wiring."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_decal_chain2.log")
BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def pin_val(pin):
    try:
        return unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or ""
    except Exception:
        return ""


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP)
    graph = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "Fire_HitScan")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    cast1 = next(n for n in editor.list_all_nodes() if n.get_name() == "K2Node_DynamicCast_1")
    for pin_name in ("then", "CastFailed", "AsSkeletalMeshComponent", "bSuccess"):
        pin = cast1.find_output_pin(pin_name)
        if not pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"Cast1 {pin_name} -> {n.get_name() if n else '?'} | {title(n) if n else ''}")

    for node_name in ("K2Node_CallFunction_61", "K2Node_CallFunction_63"):
        node = next(n for n in editor.list_all_nodes() if n.get_name() == node_name)
        log(f"{node_name} decal={pin_val(node.find_input_pin('DecalMaterial'))!r}")
        exe = node.find_input_pin("execute")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exe):
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  exec in <- {n.get_name() if n else '?'}")
        then = node.find_output_pin("then")
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  then -> {n.get_name() if n else '?'}")

    log("done")


main()
