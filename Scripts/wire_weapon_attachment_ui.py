"""Attach SCARWeaponAttachmentComponent to BP_FPCharacter for on-screen attachment toggles."""
import unreal
from pathlib import Path

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"
BP_ASSET = f"{BP_PATH}.BP_FPCharacter"
COMPONENT_CLASS = "/Script/SCAR.SCARWeaponAttachmentComponent"
LOG_PATH = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/wire_weapon_attachment_ui.log")


def log(msg: str) -> None:
    LOG_PATH.write_text(LOG_PATH.read_text() + msg + "\n" if LOG_PATH.exists() else msg + "\n")
    unreal.log(f"[weapon_attachments] {msg}")


def blueprint_has_component(bp, class_name_substring: str) -> bool:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if obj and class_name_substring in obj.get_class().get_name():
            return True
    return False


def ensure_attachment_component(bp) -> None:
    component_class = unreal.load_class(None, COMPONENT_CLASS)
    if not component_class:
        raise RuntimeError(
            "SCARWeaponAttachmentComponent not compiled yet — build the SCAR module first"
        )

    if blueprint_has_component(bp, "SCARWeaponAttachmentComponent"):
        log("BP_FPCharacter already has SCARWeaponAttachmentComponent")
        return

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0] if handles else None
    if not root_handle:
        raise RuntimeError("Could not resolve BP_FPCharacter root subobject")

    params = unreal.AddNewSubobjectParams()
    params.parent_handle = root_handle
    params.new_class = component_class
    params.blueprint_context = bp

    result, fail_reason = subsystem.add_new_subobject(params)
    if fail_reason and str(fail_reason).strip():
        raise RuntimeError(f"Failed to add SCARWeaponAttachmentComponent: {fail_reason}")

    subsystem.rename_subobject(result, "SCARWeaponAttachment")
    log("Added SCARWeaponAttachmentComponent to BP_FPCharacter")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    bp = unreal.load_asset(BP_ASSET)
    if not bp:
        raise RuntimeError(f"Missing {BP_ASSET}")

    ensure_attachment_component(bp)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(BP_PATH, only_if_is_dirty=False)
    log("Done — attachment toggle bar appears bottom-right during play")


main()
