"""Import custom pistol fire SFX and assign it to BP_Weapon_Pistol."""

import unreal

WAV_PATH = "/Users/nickortiz/Documents/Unreal Projects/SCAR/Content/BodycamFPSKIT/Audio/Pistol_Audio/Pistol-SFX.wav"
DEST_PATH = "/Game/BodycamFPSKIT/Audio/Pistol_Audio"
WAVE_NAME = "Pistol-SFX"
BLUEPRINT_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol"


def import_sound_wave() -> unreal.SoundWave:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    existing = f"{DEST_PATH}/{WAVE_NAME}.{WAVE_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(existing):
        unreal.log(f"Replacing existing asset: {existing}")
        unreal.EditorAssetLibrary.delete_asset(existing)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", WAV_PATH)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", WAVE_NAME)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    asset_tools.import_asset_tasks([task])

    imported_objects = task.get_editor_property("imported_object_paths")
    if not imported_objects:
        raise RuntimeError("Failed to import pistol SFX wav")

    sound_wave = unreal.load_asset(imported_objects[0])
    if not sound_wave:
        raise RuntimeError(f"Failed to load imported sound wave at {imported_objects[0]}")

    unreal.log(f"Imported sound wave: {sound_wave.get_path_name()}")
    return sound_wave


def assign_fire_sound(sound_wave: unreal.SoundWave) -> None:
    blueprint = unreal.load_asset(BLUEPRINT_PATH)
    if not blueprint:
        raise RuntimeError(f"Could not load blueprint: {BLUEPRINT_PATH}")

    generated_class = blueprint.generated_class()
    cdo = unreal.get_default_object(generated_class)
    cdo.set_editor_property("FireSound", sound_wave)
    blueprint.modify()

    unreal.EditorAssetLibrary.save_asset(BLUEPRINT_PATH, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_asset(sound_wave.get_path_name(), only_if_is_dirty=False)

    unreal.log(f"Assigned FireSound on {BLUEPRINT_PATH} -> {sound_wave.get_path_name()}")


def main() -> None:
    sound_wave = import_sound_wave()
    assign_fire_sound(sound_wave)
    unreal.log("Pistol SFX import complete.")


if __name__ == "__main__":
    main()
