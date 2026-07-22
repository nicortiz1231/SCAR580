"""Save WBP_Inventory + ABP_FP_ArmsProcedural after MCP edits; verify slots."""
from pathlib import Path
import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/save_inventory_arms_fixes.log")
ABP = "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural"
INV = "/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Switcher/WBP_Inventory"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(f"[save_fixes] {msg}")


def title(n) -> str:
    try:
        return str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        return n.get_class().get_name()


def verify_inventory():
    bp = unreal.load_asset(INV)
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    nodes = list(editor.list_all_nodes()) if hasattr(editor, "list_all_nodes") else list(eg.nodes)
    bad = []
    for n in nodes:
        t = title(n).lower()
        if "set brush" in t or "get all actors" in t or n.get_class().get_name() == "K2Node_GetArrayItem":
            bad.append(title(n))
    log(f"inventory bad_nodes={bad}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ok = unreal.EditorAssetLibrary.save_asset(INV, only_if_is_dirty=False)
    log(f"inventory saved={ok}")


def verify_abp():
    bp = unreal.load_asset(ABP)
    graphs = []
    try:
        graphs.extend(list(unreal.AnimBlueprintLibrary.get_animation_graphs(bp)))
    except Exception as exc:
        log(f"get_animation_graphs: {exc}")
    try:
        for g in bp.function_graphs:
            graphs.append(g)
    except Exception:
        pass

    defaults = []
    slots = []
    seen = set()
    for g in graphs:
        if not g:
            continue
        key = g.get_path_name()
        if key in seen:
            continue
        seen.add(key)
        try:
            nodes = list(g.nodes)
        except Exception:
            nodes = list(g.get_editor_property("nodes"))
        for n in nodes:
            if "Slot" not in n.get_class().get_name():
                continue
            t = title(n)
            slots.append((n.get_name(), t))
            if "DefaultSlot" in t:
                defaults.append((n.get_name(), t))
            log(f"SLOT {g.get_name()}::{n.get_name()} :: {t}")

    log(f"DefaultSlot count={len(defaults)} total_slots={len(slots)}")
    if len(defaults) > 1:
        # Keep first; rename others
        for name, t in defaults[1:]:
            log(f"WARNING still duplicate: {name} {t}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ok = unreal.EditorAssetLibrary.save_asset(ABP, only_if_is_dirty=False)
    log(f"abp saved={ok}")


def main():
    if LOG.exists():
        LOG.unlink()
    log("=== start ===")
    verify_inventory()
    verify_abp()
    log("=== done ===")


main()
