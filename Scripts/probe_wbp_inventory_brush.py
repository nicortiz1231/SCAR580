"""Probe WBP_Inventory EventGraph for SetBrushFromMaterial / Array_Get None error."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_wbp_inventory_brush.log")
BP_PATH = "/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Switcher/WBP_Inventory"


def log(msg: str) -> None:
    existing = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(existing + msg + "\n", encoding="utf-8")
    unreal.log(f"[probe_wbp_inventory_brush] {msg}")


def pin_name(pin) -> str:
    try:
        return str(pin.get_name())
    except Exception:
        return "?"


def dump_node(node, indent: str = "") -> None:
    title = ""
    try:
        title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
    except Exception:
        title = node.get_class().get_name()
    log(f"{indent}NODE {node.get_name()} class={node.get_class().get_name()} title={title}")
    try:
        for pin in node.get_pins():
            direction = pin.get_pin_direction()
            dir_s = "OUT" if direction == unreal.EdGraphPinDirection.EGPD_OUTPUT else "IN"
            links = []
            try:
                for lp in pin.get_linked_to():
                    own = lp.get_owning_node()
                    links.append(f"{own.get_name()}.{pin_name(lp)}")
            except Exception as exc:
                links.append(f"err:{exc}")
            default = ""
            try:
                default = str(pin.default_value)
            except Exception:
                pass
            log(f"{indent}  {dir_s} {pin_name(pin)} links={links} default={default!r}")
    except Exception as exc:
        log(f"{indent}  pin dump failed: {exc}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    bp = unreal.load_asset(BP_PATH)
    if not bp:
        log(f"Failed to load {BP_PATH}")
        return

    log(f"Loaded {BP_PATH}")
    # Variables
    try:
        for var in bp.new_variables:
            log(f"VAR {var.var_name} type={var.var_type.pin_category}/{var.var_type.pin_sub_category_object}")
    except Exception as exc:
        log(f"var dump failed: {exc}")

    graphs = []
    try:
        eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        if eg:
            graphs.append(eg)
    except Exception as exc:
        log(f"find_event_graph: {exc}")

    try:
        for g in bp.function_graphs:
            graphs.append(g)
    except Exception:
        pass

    for g in graphs:
        log(f"=== GRAPH {g.get_name()} ===")
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        nodes = editor.get_nodes() if hasattr(editor, "get_nodes") else list(g.nodes)
        for node in nodes:
            cls = node.get_class().get_name()
            title = ""
            try:
                title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
            except Exception:
                pass
            interesting = any(
                k in f"{cls} {title} {node.get_name()}".lower()
                for k in (
                    "brush",
                    "material",
                    "array",
                    "construct",
                    "setup",
                    "preview",
                    "character",
                )
            )
            if interesting:
                dump_node(node)


if __name__ == "__main__":
    main()
