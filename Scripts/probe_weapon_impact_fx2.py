"""Trace exec chains for impact FX nodes in Fire_HitScan."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_impact_fx2.log")
BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"
TARGETS = {
    "K2Node_CallFunction_32",
    "K2Node_CallFunction_33",
    "K2Node_CallFunction_19",
    "K2Node_CallFunction_61",
    "K2Node_CallFunction_63",
    "K2Node_CallFunction_10693",
}


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def pin_val(pin):
    try:
        return unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
    except Exception:
        return ""


def exec_out_pins(node):
    pins = []
    for pin in node.get_pins():
        if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
            continue
        name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if name == "then" or name.startswith("then_") or name == "else" or name == "Completed":
            pins.append(pin)
    return pins


def exec_in_pin(node):
    return node.find_input_pin("execute")


def upstream_exec(node):
    pin = exec_in_pin(node)
    if not pin:
        return []
    out = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
        if owner:
            out.append((owner, lp))
    return out


def downstream_exec(node):
    out = []
    for pin in exec_out_pins(node):
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
            if owner:
                out.append((owner, pin, lp))
    return out


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP)
    graph = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(bp) if g.get_name() == "Fire_HitScan")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    for node in editor.list_all_nodes():
        if node.get_name() not in TARGETS:
            continue
        log(f"=== {node.get_name()} | {title(node)} ===")
        for pin_name in ("SystemTemplate", "DecalMaterial", "NiagaraSystem"):
            pin = node.find_input_pin(pin_name)
            if pin:
                log(f"  {pin_name}={pin_val(pin)!r}")
        log("  upstream:")
        for owner, lp in upstream_exec(node):
            log(f"    {owner.get_name()} | {title(owner)} -> {str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        log("  downstream:")
        for owner, op, lp in downstream_exec(node):
            log(f"    {str(unreal.BlueprintGraphPinLibrary.get_pin_name(op))} -> {owner.get_name()} | {title(owner)}")

    # Bullet casing anywhere on blueprint
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            t = title(node)
            if "BulletCasing" in t or "ShellEject" in t or "NS_WeaponFire_Shell" in pin_val(node.find_input_pin("SystemTemplate") or node.find_input_pin("NiagaraSystem") or node):
                log(f"GRAPH {graph.get_name()} {node.get_name()} | {t}")


main()
