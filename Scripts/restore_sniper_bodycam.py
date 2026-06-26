"""Restore sniper visuals to original Bodycam Map_Test pickup behavior."""
import shutil
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/restore_sniper_bodycam.log")
ORIG = Path("/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Content/BodycamFPSKIT/Blueprints/Interactables")
SCAR = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Content/BodycamFPSKIT/Blueprints/Interactables")
CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter"

# Matches BP_Weapon_Pickup_Sniper defaults (HOLOSIGHT + laser + suppressor)
PICKUP_ATTACHMENTS = (
    "(Sight_37_688233D743AA415C91250EBC240B11ED=NewEnumerator1,"
    "Laser_38_3209213B48BBF0256E8473A33CC4C0FE=NewEnumerator1,"
    "Muzzle_42_288332C341D7A8B7E31632867A1FE4DB=NewEnumerator1,"
    "Grip_46_62A21AB489496DC33D1ACDA661CA2D84=NewEnumerator0)"
)

SPAWN_CHAINS = (
    ("K2Node_CallFunction_140", "K2Node_VariableGet_133"),
    ("K2Node_CallFunction_141", "K2Node_VariableGet_83"),
)

RESTORE_FILES = (
    (ORIG / "Sniper/BP_Weapon_Sniper.uasset", SCAR / "Sniper/BP_Weapon_Sniper.uasset"),
    (ORIG / "Sniper/DT_SniperAnimationValues.uasset", SCAR / "Sniper/DT_SniperAnimationValues.uasset"),
    (ORIG / "BP_Item_Base.uasset", SCAR / "BP_Item_Base.uasset"),
)


def log(msg: str) -> None:
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(f"[restore_sniper] {msg}")


def connect_exec(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def restore_assets() -> None:
    for src, dst in RESTORE_FILES:
        if not dst.exists():
            if not src.exists():
                raise FileNotFoundError(f"Missing original asset: {src}")
            shutil.copy2(src, dst)
        log(f"Using restored {dst.name} on disk ({dst.stat().st_size} bytes)")


def fix_hands_slot(char_bp) -> None:
    for graph in unreal.BlueprintEditorLibrary.list_graphs(char_bp):
        if graph.get_name() != "BeginSetup":
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pname.startswith("ItemData_Attachments"):
                    pin.set_pin_value(PICKUP_ATTACHMENTS)
                    log(f"HandsSlot attachments -> Map_Test pickup defaults")
                    return
    log("WARN: HandsSlot construct node not found")


def reconnect_spawn_chains(char_bp) -> None:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    for spawn_name, get_name in SPAWN_CHAINS:
        spawn_att = None
        var_get = None
        for node in editor.list_all_nodes():
            if node.get_name() == spawn_name:
                spawn_att = node
            if node.get_name() == get_name:
                var_get = node
        if not spawn_att or not var_get:
            log(f"SKIP reconnect {spawn_name}")
            continue
        then = spawn_att.find_output_pin("then")
        exec_in = var_get.find_input_pin("execute")
        if not then or not exec_in:
            continue
        linked = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(then))
        if linked and any(lp.get_owning_node().get_name() == get_name for lp in linked):
            log(f"{spawn_name} already connected")
            continue
        then.break_pin_links()
        if connect_exec(then, exec_in):
            log(f"Reconnected {spawn_name} -> {get_name}")


def verify_sniper_defaults() -> None:
    sniper = unreal.load_asset(
        "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
    )
    cdo = unreal.get_default_object(sniper.generated_class())
    aim = cdo.get_editor_property("AimDistanceFromCamera")
    optic = cdo.get_editor_property("OpticSightMesh")
    scope = cdo.get_editor_property("ScopeSightMesh")
    log(f"Sniper AimDistanceFromCamera={aim}")
    log(f"Sniper OpticSightMesh={optic.get_name() if optic else None}")
    log(f"Sniper ScopeSightMesh={scope.get_name() if scope else None}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()

    restore_assets()

    unreal.EditorAssetLibrary.save_loaded_asset(
        unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
    )

    char_bp = unreal.load_asset(f"{CHAR_BP}.BP_FPCharacter")
    fix_hands_slot(char_bp)
    reconnect_spawn_chains(char_bp)

    item_bp = unreal.load_asset(
        "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"
    )
    for bp, path in (
        (char_bp, CHAR_BP),
        (item_bp, "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base"),
        (unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"),
         "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper"),
    ):
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)

    verify_sniper_defaults()
    log("Done")


main()
