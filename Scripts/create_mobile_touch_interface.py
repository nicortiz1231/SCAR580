"""Update TI_MobileCombat: DefaultVirtualJoysticks look + mockup 3-zone layout."""
import unreal
from pathlib import Path

TI_PATH = "/Game/SCAR580/Input/TI_MobileCombat"
DEFAULT_TI = "/Engine/MobileResources/HUD/DefaultVirtualJoysticks.DefaultVirtualJoysticks"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/create_mobile_touch_interface.log")

THUMB_TEX = "/Engine/MobileResources/HUD/VirtualJoystick_Thumb.VirtualJoystick_Thumb"
BG_TEX = "/Engine/MobileResources/HUD/VirtualJoystick_Background.VirtualJoystick_Background"

# Equal thirds along bottom — matches ADS/Reload/Shoot mockup spacing.
LEFT_X = 0.17
CENTER_X = 0.50
RIGHT_X = 0.83
BOTTOM_Y = -0.28


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[touch_interface] {msg}")


def make_key(name: str) -> unreal.Key:
    key = unreal.Key()
    key.set_editor_property("key_name", unreal.Name(name))
    return key


def joystick_textures():
    thumb = unreal.load_asset(THUMB_TEX)
    bg = unreal.load_asset(BG_TEX)
    return thumb, bg


def clone_control(src: unreal.TouchInputControl) -> unreal.TouchInputControl:
    dst = unreal.TouchInputControl()
    for prop in (
        "bTreatAsButton",
        "image1",
        "image2",
        "visual_size",
        "thumb_size",
        "interaction_size",
        "input_scale",
        "main_input_key",
        "alt_input_key",
    ):
        try:
            dst.set_editor_property(prop, src.get_editor_property(prop))
        except Exception:
            pass
    return dst


def apply_joystick_look(c: unreal.TouchInputControl) -> None:
    """Match DefaultVirtualJoysticks circle + knob art (user reference screenshot)."""
    thumb, bg = joystick_textures()
    c.set_editor_property("image1", thumb)
    c.set_editor_property("image2", bg)


def make_move_joystick(default_controls, center_x: float, center_y: float) -> unreal.TouchInputControl:
    stick = clone_control(default_controls[0])
    stick.set_editor_property("Center", unreal.Vector2D(center_x, center_y))
    apply_joystick_look(stick)
    return stick


def make_joystick_button(center_x: float, center_y: float, key_name: str, default_controls) -> unreal.TouchInputControl:
    """Tap button using the same ring/knob visuals as DefaultVirtualJoysticks."""
    ref = default_controls[0]
    c = unreal.TouchInputControl()
    c.set_editor_property("bTreatAsButton", True)
    c.set_editor_property("Center", unreal.Vector2D(center_x, center_y))
    c.set_editor_property("VisualSize", ref.get_editor_property("visual_size"))
    c.set_editor_property("ThumbSize", ref.get_editor_property("thumb_size"))
    c.set_editor_property("InteractionSize", ref.get_editor_property("interaction_size"))
    c.set_editor_property("InputScale", unreal.Vector2D(1.0, 1.0))
    c.set_editor_property("MainInputKey", make_key(key_name))
    apply_joystick_look(c)
    return c


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    default = unreal.load_asset(f"{DEFAULT_TI}.DefaultVirtualJoysticks")
    if not default:
        raise RuntimeError(f"Missing {DEFAULT_TI}")
    default_controls = list(default.get_editor_property("controls"))

    ti = unreal.load_asset(f"{TI_PATH}.TI_MobileCombat")
    if not ti:
        raise RuntimeError(f"Missing {TI_PATH}")

    controls = [
        make_move_joystick(default_controls, LEFT_X, BOTTOM_Y),
        make_joystick_button(CENTER_X, BOTTOM_Y, "R", default_controls),
        make_joystick_button(RIGHT_X, BOTTOM_Y, "LeftMouseButton", default_controls),
    ]
    ti.set_editor_property("controls", controls)
    ti.set_editor_property("active_opacity", default.get_editor_property("active_opacity"))
    ti.set_editor_property("inactive_opacity", default.get_editor_property("inactive_opacity"))
    ti.set_editor_property("time_until_deactive", default.get_editor_property("time_until_deactive"))
    ti.set_editor_property("time_until_reset", default.get_editor_property("time_until_reset"))
    ti.set_editor_property("activation_delay", default.get_editor_property("activation_delay"))
    ti.set_editor_property("startup_delay", default.get_editor_property("startup_delay"))

    unreal.EditorAssetLibrary.save_asset(TI_PATH, only_if_is_dirty=False)
    log(
        "Updated TI_MobileCombat: DefaultVirtualJoysticks visuals — "
        "left move stick, center reload (R), right shoot (LMB)"
    )


main()
