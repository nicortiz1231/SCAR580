"""Create TI_MobileCombat with 3 bottom buttons: ADS (Shift), Reload (R), Shoot (LMB)."""
import unreal
from pathlib import Path

TI_PATH = "/Game/SCAR580/Input/TI_MobileCombat"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/create_mobile_touch_interface.log")

BTN_TEX = "/Engine/MobileResources/HUD/MobileHUDButton1_off.MobileHUDButton1_off"
BTN_TEX_ON = "/Engine/MobileResources/HUD/MobileHUDButton1_on.MobileHUDButton1_on"


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[touch_interface] {msg}")


def make_key(name: str) -> unreal.Key:
    key = unreal.Key()
    key.set_editor_property("key_name", unreal.Name(name))
    return key


def make_control(center_x: float, center_y: float, key_name: str) -> unreal.TouchInputControl:
    img = unreal.load_asset(BTN_TEX)
    img_on = unreal.load_asset(BTN_TEX_ON)
    c = unreal.TouchInputControl()
    c.set_editor_property("bTreatAsButton", True)
    c.set_editor_property("Center", unreal.Vector2D(center_x, center_y))
    c.set_editor_property("VisualSize", unreal.Vector2D(0.22, 0.22))
    c.set_editor_property("ThumbSize", unreal.Vector2D(0.22, 0.22))
    c.set_editor_property("InteractionSize", unreal.Vector2D(0.24, 0.24))
    c.set_editor_property("InputScale", unreal.Vector2D(1.0, 1.0))
    c.set_editor_property("MainInputKey", make_key(key_name))
    c.set_editor_property("Image1", img_on or img)
    c.set_editor_property("Image2", img)
    return c


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    dest = "/Game/SCAR580/Input"
    unreal.EditorAssetLibrary.make_directory(dest)

    ti = unreal.load_asset(f"{TI_PATH}.TI_MobileCombat")
    if not ti:
        factory = unreal.TouchInterfaceFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        ti = asset_tools.create_asset("TI_MobileCombat", dest, unreal.TouchInterface, factory)
    if not ti:
        raise RuntimeError("Could not create TI_MobileCombat")

    # Relative coords: x 0-1 left->right; negative y = distance from bottom edge.
    # Bottom row, equal thirds — matches mockup (ADS / Reload / Shoot).
    controls = [
        make_control(0.17, -0.28, "LeftShift"),       # ADS = Shift
        make_control(0.50, -0.28, "R"),               # Reload = R
        make_control(0.83, -0.28, "LeftMouseButton"), # Shoot = LMB
    ]
    ti.set_editor_property("controls", controls)
    ti.set_editor_property("active_opacity", 0.85)
    ti.set_editor_property("inactive_opacity", 0.55)
    ti.set_editor_property("time_until_deactive", 2.0)
    ti.set_editor_property("time_until_reset", 0.0)
    ti.set_editor_property("activation_delay", 0.0)
    ti.set_editor_property("startup_delay", 0.0)

    unreal.EditorAssetLibrary.save_asset(TI_PATH, only_if_is_dirty=False)
    log(f"Saved {TI_PATH} with {len(controls)} controls (Shift / R / LMB)")


main()
