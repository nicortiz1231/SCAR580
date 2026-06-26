"""Probe BP_Item_Base Fire_HitScan for impact debris/spark/decal nodes."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_impact_fx.log")
BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def pin_val(pin):
    try:
        return unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
    except Exception:
        return "?"


def walk_exec(start, max_hops=40):
    seen = set()
    cur = start
    hops = 0
    while cur and hops < max_hops:
        name = cur.get_name()
        if name in seen:
            log(f"  loop {name}")
            break
        seen.add(name)
        log(f"  exec {name} | {title(cur)}")
        then = None
        for pin_name in ("then", "else", "Completed"):
            p = cur.find_output_pin(pin_name)
            if p and unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                then = p
                break
        if not then:
            for p in cur.get_pins():
                if unreal.BlueprintGraphPinLibrary.get_pin_direction(p) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                    continue
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                if pname in ("execute", "self") or not pname.startswith("then"):
                    if pname.startswith("then") or pname == "else":
                        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(p)
                        if links:
                            then = p
                            break
        if not then:
            break
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
        if not links:
            break
        cur = unreal.BlueprintGraphPinLibrary.get_owning_node(links[0])
        hops += 1


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP)
    graph = None
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() == "Fire_HitScan":
            graph = g
            break
    if not graph:
        log("Fire_HitScan not found")
        return

    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in editor.list_all_nodes():
        t = title(node)
        cls = node.get_class().get_name()
        if any(
            k in t
            for k in (
                "SpawnDecal",
                "SpawnSystem",
                "Niagara",
                "Impact",
                "Decal",
                "BulletCasing",
                "Shell",
                "Tracer",
            )
        ) or cls in ("K2Node_CallFunction", "K2Node_SpawnActorFromClass"):
            log(f"NODE {node.get_name()} | {cls} | {t}")
            for pin_name in ("execute", "WorldContextObject", "SystemTemplate", "DecalMaterial", "NiagaraSystem"):
                pin = node.find_input_pin(pin_name)
                if pin:
                    links = [
                        unreal.BlueprintGraphPinLibrary.get_owning_node(lp).get_name()
                        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
                        if unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
                    ]
                    log(f"  in {pin_name}: default={pin_val(pin)!r} links={links}")

    entry = next(
        (n for n in editor.list_all_nodes() if n.get_class().get_name() == "K2Node_FunctionEntry"),
        None,
    )
    if entry:
        log("=== exec from entry ===")
        then = entry.find_output_pin("then")
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
        if links:
            walk_exec(unreal.BlueprintGraphPinLibrary.get_owning_node(links[0]))

    log("done")


main()
