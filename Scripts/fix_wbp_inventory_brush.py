"""Fix WBP_Inventory Construct: remove unsafe Array_Get → SetBrushFromMaterial chain."""

from __future__ import annotations

from pathlib import Path

import unreal

LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_wbp_inventory_brush.log")
BP_PATH = "/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Switcher/WBP_Inventory"


def log(msg: str) -> None:
    existing = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""
    LOG_PATH.write_text(existing + msg + "\n", encoding="utf-8")
    unreal.log(f"[fix_wbp_inventory_brush] {msg}")


def title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        try:
            return str(node.get_node_title()).replace("\n", " | ")
        except Exception:
            return node.get_class().get_name()


def find_pin(node, names, direction_out=None):
    names_l = [n.lower() for n in names]
    # Prefer BlueprintGraphEditor helpers if present
    for name in names:
        for getter in ("find_output_pin", "find_input_pin"):
            if direction_out is True and getter != "find_output_pin":
                continue
            if direction_out is False and getter != "find_input_pin":
                continue
            fn = getattr(node, getter, None)
            if not fn:
                continue
            try:
                pin = fn(name)
                if pin:
                    return pin
            except Exception:
                pass

    pins_fn = getattr(node, "get_pins", None) or getattr(node, "pins", None)
    pins = []
    try:
        if callable(pins_fn):
            pins = list(pins_fn())
        elif pins_fn is not None:
            pins = list(pins_fn)
    except Exception:
        pins = []

    for pin in pins:
        try:
            pname = str(pin.get_name()).lower()
        except Exception:
            continue
        if pname not in names_l:
            continue
        if direction_out is None:
            return pin
        is_out = pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT
        if direction_out == is_out:
            return pin
    return None


def break_links(pin) -> bool:
    if not pin:
        return False
    for fn_name in ("break_all_pin_links", "break_pin_links"):
        fn = getattr(pin, fn_name, None)
        if not fn:
            continue
        try:
            fn(True)
            return True
        except TypeError:
            try:
                fn()
                return True
            except Exception:
                pass
        except Exception:
            pass
    try:
        unreal.BlueprintGraphPinLibrary.break_all_pin_links(pin, True)
        return True
    except Exception as exc:
        log(f"break_links failed: {exc}")
        return False


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_PATH)
    if not bp:
        raise RuntimeError(f"Missing {BP_PATH}")

    event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    if not event_graph:
        raise RuntimeError("No EventGraph on WBP_Inventory")

    editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
    if hasattr(editor, "list_all_nodes"):
        nodes = list(editor.list_all_nodes())
    else:
        nodes = list(event_graph.get_editor_property("nodes"))

    setup = None
    get_actors = None
    array_get = None
    get_mat = None
    get_preview_img = None
    set_brush = None

    for n in nodes:
        t = title(n).lower()
        cls = n.get_class().get_name()
        name = n.get_name()
        if name == "K2Node_CallFunction_0" or (
            cls == "K2Node_CallFunction" and t.startswith("setup") and "inventory" in t
        ):
            setup = n
        elif name == "K2Node_CallFunction_1" or (
            cls == "K2Node_CallFunction" and "get all actors of class" in t
        ):
            get_actors = n
        elif name == "K2Node_GetArrayItem_0" or cls == "K2Node_GetArrayItem":
            array_get = n
        elif name == "K2Node_VariableGet_0" or (
            cls == "K2Node_VariableGet" and "materialinstance" in t
        ):
            get_mat = n
        elif name == "K2Node_VariableGet_1" or (
            cls == "K2Node_VariableGet" and "characterpreview" in t
        ):
            get_preview_img = n
        elif name == "K2Node_CallFunction_7" or (
            cls == "K2Node_CallFunction" and "set brush from material" in t
        ):
            set_brush = n

    log(f"setup={getattr(setup,'get_name',lambda:None)()}")
    log(f"get_actors={getattr(get_actors,'get_name',lambda:None)()}")
    log(f"set_brush={getattr(set_brush,'get_name',lambda:None)()}")

    if setup:
        then_pin = find_pin(setup, ["then"], direction_out=True)
        if then_pin and break_links(then_pin):
            log("Broke Setup.then so Construct no longer reaches GetAllActors/SetBrush")
        else:
            log("Warning: could not break Setup.then")

    to_remove = [n for n in (set_brush, get_actors, array_get, get_mat, get_preview_img) if n]
    removed = 0
    for node in to_remove:
        name = node.get_name()
        try:
            if hasattr(editor, "remove_nodes"):
                editor.remove_nodes([node])
            elif hasattr(editor, "remove_node"):
                editor.remove_node(node)
            else:
                event_graph.remove_node(node)
            removed += 1
            log(f"Removed {name} ({title(node)})")
        except Exception as exc:
            log(f"Failed removing {name}: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log(f"Done. removed={removed} saved={saved}")


if __name__ == "__main__":
    main()
