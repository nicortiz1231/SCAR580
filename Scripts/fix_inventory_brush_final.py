"""Fix WBP_Inventory on whatever editor instance Cmd forwards into."""
from pathlib import Path
import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_inventory_brush_final.log")
INV = "/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Switcher/WBP_Inventory"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(f"[fix_inv] {msg}")
    print(msg)


def title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        try:
            return str(node.get_node_title()).replace("\n", " | ")
        except Exception:
            return node.get_class().get_name()


def find_pin(node, name: str, want_out=None):
    # BlueprintEditorLibrary.list_all_pins
    pins = []
    try:
        pins = list(unreal.BlueprintEditorLibrary.list_all_pins(node))
    except Exception:
        pass
    for getter in ("find_output_pin", "find_input_pin", "get_pins"):
        fn = getattr(node, getter, None)
        if not fn:
            continue
        try:
            if getter == "get_pins":
                pins = list(fn())
            else:
                pin = fn(name)
                if pin:
                    return pin
        except Exception:
            pass
    for pin in pins:
        try:
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        except Exception:
            try:
                pname = str(pin.get_name())
            except Exception:
                continue
        if pname != name:
            continue
        if want_out is None:
            return pin
        try:
            direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            is_out = direction == unreal.EdGraphPinDirection.EGPD_OUTPUT
        except Exception:
            try:
                is_out = pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT
            except Exception:
                continue
        if is_out == want_out:
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
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(INV)
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    nodes = list(editor.list_all_nodes())

    setup = None
    remove = []
    for n in nodes:
        t = title(n).lower()
        cls = n.get_class().get_name()
        name = n.get_name()
        log(f"NODE {name} {cls} :: {title(n)}")
        if name == "K2Node_CallFunction_0":
            setup = n
        if name in (
            "K2Node_CallFunction_1",
            "K2Node_CallFunction_7",
            "K2Node_GetArrayItem_0",
            "K2Node_VariableGet_0",
            "K2Node_VariableGet_1",
        ):
            remove.append(n)
        elif "set brush from material" in t or "get all actors of class" in t:
            remove.append(n)
        elif cls == "K2Node_GetArrayItem":
            remove.append(n)
        elif cls == "K2Node_VariableGet" and (
            "materialinstance" in t or "characterpreview" in t
        ):
            remove.append(n)

    if setup:
        then_pin = find_pin(setup, "then", want_out=True)
        if break_links(then_pin):
            log("Broke Setup.then")
        else:
            log("Could not break Setup.then")

    removed = 0
    for n in remove:
        name = n.get_name()
        try:
            if hasattr(editor, "remove_nodes"):
                editor.remove_nodes([n])
            elif hasattr(editor, "remove_node"):
                editor.remove_node(n)
            else:
                raise RuntimeError("no remove_node on editor")
            removed += 1
            log(f"Removed {name}")
        except Exception as exc:
            log(f"Failed {name}: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_asset(INV, only_if_is_dirty=False)
    log(f"removed={removed} saved={saved}")

    nodes = list(editor.list_all_nodes())
    for n in nodes:
        log(f"AFTER {n.get_name()} :: {title(n)}")


main()
