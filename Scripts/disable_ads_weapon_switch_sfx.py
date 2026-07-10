"""Remove ADS enter/exit and weapon-switch zoom SFX from BP_FPCharacter."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/disable_ads_weapon_switch_sfx.log")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"

FOV_SOUND_NODE = "K2Node_CallFunction_27"
FOV_EVENT_NAMES = ("FOV",)
SOUND_FN_NAMES = (
    "PlaySoundAtLocation",
    "SpawnSoundAtLocation",
    "PlaySound2D",
    "SpawnSound2D",
)

MARKER = "SCAR disabled ADS/weapon-switch SFX v2"


def log(msg: str) -> None:
    prev = LOG.read_text() if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n")
    unreal.log(f"[disable_ads_weapon_sfx] {msg}")


def title(node) -> str:
    return str(node.get_node_title()).replace("\n", " | ")


def exec_out_pins(node):
    pins = []
    for pin_name in ("then", "else", "Completed"):
        pin = node.find_output_pin(pin_name)
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
    if not upstream:
        return False

    downstream = []
    for out_pin in exec_out_pins(node):
        downstream.extend(unreal.BlueprintGraphPinLibrary.list_connected_pins(out_pin))

    unreal.BlueprintGraphPinLibrary.break_pin_links(exec_in)
    for out_pin in exec_out_pins(node):
        unreal.BlueprintGraphPinLibrary.break_pin_links(out_pin)

    for up_pin in upstream:
        for down_pin in downstream:
            up_pin.try_create_connection(down_pin)

    return True


def upstream_has_fov(node, depth=0, seen=None) -> bool:
    if seen is None:
        seen = set()
    nid = id(node)
    if nid in seen or depth > 10:
        return False
    seen.add(nid)

    t = title(node)
    if any(name == t or f" | {name}" in t for name in FOV_EVENT_NAMES):
        return True
    if " | FOV" in t and node.get_class().get_name() in {
        "K2Node_CustomEvent",
        "K2Node_CallFunction",
    }:
        return True

    exec_in = exec_in_pin(node)
    if not exec_in:
        return False

    for pin in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
        if upstream_has_fov(pin.get_owning_node(), depth + 1, seen):
            return True
    return False


def is_fov_zoom_sound(node) -> bool:
    if node.get_name() == FOV_SOUND_NODE:
        return True
    t = title(node)
    if not any(name in t for name in SOUND_FN_NAMES):
        return False
    return upstream_has_fov(node)


def pin_has_links(pin) -> bool:
    return bool(unreal.BlueprintGraphPinLibrary.list_connected_pins(pin))


def remove_orphan_data_nodes(editor) -> int:
    removed = 0
    orphans = []
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        if cls not in {"K2Node_VariableGet", "K2Node_CallFunction"}:
            continue
        if cls == "K2Node_VariableGet" and "Get Sound" not in title(node):
            continue
        if cls == "K2Node_CallFunction" and "Get Sound" not in title(node):
            continue

        has_exec = exec_in_pin(node) is not None
        if has_exec:
            continue

        linked = False
        for pin in node.get_all_pins():
            if pin_has_links(pin):
                linked = True
                break
        if not linked:
            orphans.append(node)

    if orphans:
        editor.remove_nodes(orphans)
        removed = len(orphans)
        log(f"Removed {removed} orphaned data node(s)")
    return removed


def disable_fov_zoom_sound(editor, graph_name: str) -> int:
    targets = [node for node in editor.list_all_nodes() if is_fov_zoom_sound(node)]
    if not targets:
        return 0

    changed = 0
    for node in targets:
        if not bypass_exec_node(node):
            continue
        log(f"Bypassed {graph_name} {node.get_name()} | {title(node)}")
        editor.remove_nodes([node])
        log(f"Removed {graph_name} {node.get_name()}")
        changed += 1

    changed += remove_orphan_data_nodes(editor)
    return changed


def clear_sound_variable_defaults(bp) -> int:
    changed = 0
    cdo = unreal.get_default_object(bp.generated_class())
    for prop in ("Sound", "ZoomSound", "FOVSound"):
        try:
            val = cdo.get_editor_property(prop)
        except Exception:
            continue
        if val is None:
            continue
        cdo.set_editor_property(prop, None)
        log(f"Cleared CDO {prop}")
        changed += 1
    return changed


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    if not bp:
        raise RuntimeError(f"Missing {CHAR_BP}")

    total = 0
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        count = disable_fov_zoom_sound(editor, graph.get_name())
        if count:
            log(f"{graph.get_name()}: {count} change(s)")
        total += count

    total += clear_sound_variable_defaults(bp)

    if total:
        bp.modify()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(CHAR_BP, only_if_is_dirty=False)
        log(f"{MARKER}: applied {total} change(s)")
    else:
        log("No FOV zoom SFX nodes found")


main()
