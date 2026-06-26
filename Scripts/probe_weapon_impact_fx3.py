"""Find BulletCasingSys and impact FX exec wiring."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_impact_fx3.log")
ASSETS = [
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base", "Fire_HitScan"),
    ("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter", None),
]


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def pin_val(pin):
    if not pin:
        return ""
    try:
        return unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or ""
    except Exception:
        return ""


def bypass_info(editor, node_name):
    node = next((n for n in editor.list_all_nodes() if n.get_name() == node_name), None)
    if not node:
        return
    log(f"--- {node_name} | {title(node)} ---")
    for pin_name in ("SystemTemplate", "DecalMaterial"):
        pin = node.find_input_pin(pin_name)
        if pin:
            log(f"  {pin_name}={pin_val(pin)!r}")
    exe = node.find_input_pin("execute")
    if exe:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exe):
            up = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  exec in <- {up.get_name() if up else '?'}")
    then = node.find_output_pin("then")
    if then:
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
            down = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            log(f"  then -> {down.get_name() if down else '?'}")


def scan_graph(bp_path, graph_name=None):
    bp = unreal.load_asset(bp_path)
    graphs = unreal.BlueprintEditorLibrary.list_graphs(bp)
    if graph_name:
        graphs = [g for g in graphs if g.get_name() == graph_name]
    for graph in graphs:
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            t = title(node)
            st = pin_val(node.find_input_pin("SystemTemplate"))
            dm = pin_val(node.find_input_pin("DecalMaterial"))
            if any(
                k in (t + st + dm)
                for k in (
                    "SpawnSystemAtLocation",
                    "SpawnDecalAttached",
                    "AddImpulseAtLocation",
                    "BulletCasing",
                    "ShellEject",
                    "ImpactConcrete",
                    "Impact_Decal",
                    "Tracer",
                )
            ):
                log(f"{bp_path}::{graph.get_name()} {node.get_name()} | {t}")
                if st:
                    log(f"  SystemTemplate={st!r}")
                if dm:
                    log(f"  DecalMaterial={dm!r}")
                exe = node.find_input_pin("execute")
                if exe and unreal.BlueprintGraphPinLibrary.list_connected_pins(exe):
                    log("  has exec in")
                then = node.find_output_pin("then")
                if then and unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                    log("  has exec out")


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(ASSETS[0][0])
    graph = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "Fire_HitScan")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for name in (
        "K2Node_CallFunction_32",
        "K2Node_CallFunction_61",
        "K2Node_CallFunction_10693",
        "K2Node_CallFunction_19",
        "K2Node_CallFunction_17",
        "K2Node_CallFunction_2",
    ):
        bypass_info(editor, name)

    for asset, gname in ASSETS:
        scan_graph(asset, gname)

    log("done")


main()
