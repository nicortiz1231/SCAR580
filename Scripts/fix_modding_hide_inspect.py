"""Permanently collapse the PRESS Z FOR INSPECT TextBlock in UI_WeaponModding."""
import unreal
from pathlib import Path

WBP_PATH = "/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding"
WBP_ASSET = f"{WBP_PATH}.UI_WeaponModding"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_modding_hide_inspect.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[fix_modding_hide_inspect] {msg}")


def walk_widgets(widget, depth=0):
    if not widget:
        return
    cls = widget.get_class().get_name()
    name = widget.get_name()
    if cls == "TextBlock":
        try:
            text = widget.get_editor_property("text")
            text_str = str(text)
            if "INSPECT" in text_str.upper() or "PRESS" in text_str.upper():
                widget.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
                widget.set_editor_property("text", unreal.Text(""))
                log(f"Collapsed TextBlock {name}: was {text_str!r}")
        except Exception as exc:
            log(f"TextBlock {name} ERR {exc}")

    if isinstance(widget, unreal.PanelWidget):
        for i in range(widget.get_children_count()):
            walk_widgets(widget.get_child_at(i), depth + 1)


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    wbp = unreal.load_asset(WBP_ASSET)
    if not wbp:
        raise RuntimeError(f"Missing {WBP_ASSET}")

    # WidgetTree is protected on the asset; build a temp widget instance to walk bindings.
    cls = wbp.generated_class()
    widget = unreal.WidgetBlueprintLibrary.create(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), cls)
    if not widget:
        raise RuntimeError("Could not create temp widget instance")

    try:
        wt = widget.get_editor_property("widget_tree")
    except Exception:
        wt = None

    if wt:
        root = wt.get_editor_property("root_widget")
        walk_widgets(root)
    else:
        log("No widget_tree on temp instance — runtime C++ hide will still apply")

    unreal.BlueprintEditorLibrary.compile_blueprint(wbp)
    unreal.EditorAssetLibrary.save_asset(WBP_PATH, only_if_is_dirty=False)
    log("Saved UI_WeaponModding")


main()
