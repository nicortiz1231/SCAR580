"""Disable weapon impact debris, sparks, decals, tracers, and physics impulses."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/disable_weapon_debris_sparks.log")
BP_ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"
BP_CHARACTER = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"

DISABLED_SYSTEM_SUBSTRINGS = (
    "NS_ImpactConcrete",
    "NS_WeaponFire_Tracer",
    "NS_WeaponFire_ShellEject",
)

DISABLED_DECAL_SUBSTRINGS = (
    "M_Impact_Decal",
)

MARKER = "SCAR disabled debris/sparks v1"


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[disable_weapon_debris_sparks] {msg}")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def pin_val(pin) -> str:
    if not pin:
        return ""
    try:
        return unreal.BlueprintGraphPinLibrary.get_pin_value(pin) or ""
    except Exception:
        return ""


def exec_out_pins(node):
    pins = []
    for pin_name in ("then", "else", "Completed"):
        pin = node.find_output_pin(pin_name)
        if pin:
            pins.append(pin)
    for idx in range(8):
        pin = node.find_output_pin(f"then_{idx}")
        if pin:
            pins.append(pin)
    return pins


def exec_in_pin(node):
    return node.find_input_pin("execute")


def bypass_exec_node(node) -> bool:
    exec_in = exec_in_pin(node)
    if not exec_in:
        return False

    upstream = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in))
    downstream = []
    for out_pin in exec_out_pins(node):
        downstream.extend(unreal.BlueprintGraphPinLibrary.list_connected_pins(out_pin))

    if not upstream:
        unreal.BlueprintGraphPinLibrary.break_pin_links(exec_in)
        log(f"Broke orphan exec into {node.get_name()} | {title(node)}")
        return True

    unreal.BlueprintGraphPinLibrary.break_pin_links(exec_in)
    for out_pin in exec_out_pins(node):
        unreal.BlueprintGraphPinLibrary.break_pin_links(out_pin)

    connected = False
    for up_pin in upstream:
        if not downstream:
            connected = True
            continue
        for down_pin in downstream:
            if up_pin.try_create_connection(down_pin):
                connected = True

    log(f"Bypassed exec {node.get_name()} | {title(node)}")
    return connected


def bypass_exec_chain(first_node) -> bool:
    """Skip an exec chain from first_node through its last exec node."""
    exec_in = exec_in_pin(first_node)
    if not exec_in:
        return False

    upstream = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in))
    if not upstream:
        return False

    chain = [first_node]
    cur = first_node
    for _ in range(24):
        then = cur.find_output_pin("then")
        if not then:
            break
        links = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
        if not links:
            break
        nxt = unreal.BlueprintGraphPinLibrary.get_owning_node(links[0])
        if not nxt or nxt in chain:
            break
        chain.append(nxt)
        cur = nxt

    last = chain[-1]
    downstream = []
    for out_pin in exec_out_pins(last):
        downstream.extend(unreal.BlueprintGraphPinLibrary.list_connected_pins(out_pin))

    unreal.BlueprintGraphPinLibrary.break_pin_links(exec_in)
    for node in chain:
        for out_pin in exec_out_pins(node):
            unreal.BlueprintGraphPinLibrary.break_pin_links(out_pin)

    connected = False
    if downstream:
        for up_pin in upstream:
            for down_pin in downstream:
                if up_pin.try_create_connection(down_pin):
                    connected = True
    else:
        connected = True

    log(
        f"Bypassed exec chain starting at {first_node.get_name()} | {title(first_node)} "
        f"({len(chain)} node(s))"
    )
    return connected


def break_exec_into(node) -> bool:
    exec_in = exec_in_pin(node)
    if not exec_in or not unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
        return False
    unreal.BlueprintGraphPinLibrary.break_pin_links(exec_in)
    log(f"Broke exec into {node.get_name()} | {title(node)}")
    return True


def find_spawn_nodes(editor):
    found = []
    for node in editor.list_all_nodes():
        system = pin_val(node.find_input_pin("SystemTemplate"))
        decal = pin_val(node.find_input_pin("DecalMaterial"))
        if any(sub in system for sub in DISABLED_SYSTEM_SUBSTRINGS):
            found.append(("system", node, system))
        elif any(sub in decal for sub in DISABLED_DECAL_SUBSTRINGS):
            found.append(("decal", node, decal))
    return found


def disable_graph_exec_nodes(editor, graph_name: str) -> int:
    changed = 0

    for kind, node, asset in find_spawn_nodes(editor):
        if kind == "system" and "NS_ImpactConcrete" in asset:
            if break_exec_into(node):
                changed += 1
            continue

        if kind == "system":
            if bypass_exec_chain(node):
                changed += 1
            continue

        if kind == "decal":
            if break_exec_into(node):
                changed += 1

    for node in editor.list_all_nodes():
        if "AddImpulseAtLocation" in title(node):
            if break_exec_into(node):
                changed += 1

    return changed


def disable_bullet_casing_components(bp) -> int:
    changed = 0
    try:
        cdo = unreal.get_default_object(bp.generated_class())
    except Exception:
        return 0

    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        comp_name = comp.get_name()
        class_name = comp.get_class().get_name()
        if "BulletCasing" not in comp_name and "BulletCasing" not in class_name:
            continue

        if hasattr(comp, "set_editor_property"):
            for prop in ("auto_activate", "b_auto_activate", "AutoActivate"):
                try:
                    if comp.get_editor_property(prop):
                        comp.set_editor_property(prop, False)
                        changed += 1
                        log(f"Disabled auto activate on {comp_name}.{prop}")
                except Exception:
                    pass

        if class_name == "NiagaraComponent":
            try:
                if comp.get_editor_property("asset"):
                    comp.set_editor_property("asset", None)
                    changed += 1
                    log(f"Cleared Niagara asset on {comp_name}")
            except Exception:
                pass

    return changed


def process_blueprint(bp_path: str, graph_filter=None) -> int:
    bp = unreal.load_asset(f"{bp_path}.{bp_path.split('/')[-1]}")
    if not bp:
        raise RuntimeError(f"Failed to load {bp_path}")

    changed = 0
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph_filter and graph.get_name() not in graph_filter:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        count = disable_graph_exec_nodes(editor, graph.get_name())
        if count:
            log(f"{bp_path}::{graph.get_name()} bypassed {count} node(s)")
        changed += count

    changed += disable_bullet_casing_components(bp)

    if changed:
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(bp_path, only_if_is_dirty=False)

    return changed


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    changed = process_blueprint(BP_ITEM, graph_filter={"Fire_HitScan"})
    changed += process_blueprint(BP_CHARACTER)

    if changed:
        log(f"{MARKER}: applied {changed} change(s)")
    else:
        log("No debris/spark nodes found to disable")


main()
