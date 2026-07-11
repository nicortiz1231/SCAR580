"""Add visible top-left Attachments touch button (X -> IA_Modding) to TI_MobileCombat."""
import unreal
from pathlib import Path

TI_PATH = "/Game/SCAR580/Input/TI_MobileCombat"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/setup_mobile_attachment_button.log")

LEFT_X = 0.17
CENTER_X = 0.50
RIGHT_X = 0.83
VISUAL_SIZE = 0.22
BOTTOM_Y = -(VISUAL_SIZE / 2.0)
ATTACH_X = 0.12
ATTACH_Y = 0.10
ATTACH_SIZE = 0.16


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[attachment_button] {msg}")


def make_key(name: str) -> unreal.Key:
    key = unreal.Key()
    key.set_editor_property("key_name", unreal.Name(name))
    return key


def make_button(center_x: float, center_y: float, key_name: str, size: float) -> unreal.TouchInputControl:
    c = unreal.TouchInputControl()
    c.set_editor_property("bTreatAsButton", True)
    c.set_editor_property("Center", unreal.Vector2D(center_x, center_y))
    c.set_editor_property("VisualSize", unreal.Vector2D(size, size))
    c.set_editor_property("ThumbSize", unreal.Vector2D(size, size))
    c.set_editor_property("InteractionSize", unreal.Vector2D(size + 0.03, size + 0.03))
    c.set_editor_property("InputScale", unreal.Vector2D(1.0, 1.0))
    c.set_editor_property("MainInputKey", make_key(key_name))
    c.set_editor_property("Image1", None)
    c.set_editor_property("Image2", None)
    return c


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    ti = unreal.load_asset(f"{TI_PATH}.TI_MobileCombat")
    if not ti:
        raise RuntimeError(f"Missing {TI_PATH} — run create_mobile_touch_interface.py first")

    controls = [
        make_button(LEFT_X, BOTTOM_Y, "LeftShift", VISUAL_SIZE),
        make_button(CENTER_X, BOTTOM_Y, "R", VISUAL_SIZE),
        make_button(RIGHT_X, BOTTOM_Y, "LeftMouseButton", VISUAL_SIZE),
        make_button(ATTACH_X, ATTACH_Y, "X", ATTACH_SIZE),
    ]
    ti.set_editor_property("controls", controls)
    ti.set_editor_property("active_opacity", 0.35)
    ti.set_editor_property("inactive_opacity", 0.18)
    ti.set_editor_property("time_until_deactive", 2.0)
    ti.set_editor_property("time_until_reset", 0.0)
    ti.set_editor_property("activation_delay", 0.0)
    ti.set_editor_property("startup_delay", 0.0)

    unreal.EditorAssetLibrary.save_asset(TI_PATH, only_if_is_dirty=False)
    log("Added top-left X touch zone + raised touch opacity on TI_MobileCombat")


main()
