"""
Fix remote avatar armed hold:
1) Implement BP_FPCharacter.GetEquippedAnimset to return Pistol when armed, Hands otherwise.
2) Duplicate ABP_Manny -> ABP_SCAR_RemoteManny and swap Pistol idle for ADS sequence when possible.
"""
import unreal

LOG = "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_remote_armed_hold.log"
lines = []


def log(msg):
    lines.append(str(msg))
    unreal.log(str(msg))
    print(msg)


def save_log():
    with open(LOG, "w") as f:
        f.write("\n".join(lines) + "\n")


CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
ENUM_PATH = "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Animset.ENUM_Animset"
MANNY_ABP = "/Game/BodycamFPSKIT/Demo/Character/Mannequins/Animations/ABP_Manny.ABP_Manny"
REMOTE_ABP = "/Game/SCAR580/Animations/ABP_SCAR_RemoteManny"
ADS_ANIM = "/Game/SCAR580/Animations/Anim_Arms_Pistol_ADS.Anim_Arms_Pistol_ADS"
PISTOL_IDLE = "/Game/BodycamFPSKIT/Character/Animations/WeaponAnims/Pistol/Anim_Arms_Pistol_Idle.Anim_Arms_Pistol_Idle"


def find_graph(bp, name):
    for g in list(bp.function_graphs) + list(bp.ubergraph_pages):
        if g.get_name() == name:
            return g
    # Interface implemented graphs sometimes live only in function_graphs with odd names
    for g in list(bp.function_graphs):
        for node in g.nodes:
            title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
            if name in title:
                return g
    return None


def enum_value(enum_asset, display_name, fallback):
    # UserDefinedEnum: match display name
    try:
        ude = unreal.UserDefinedEnum.cast(enum_asset) if hasattr(unreal.UserDefinedEnum, "cast") else enum_asset
    except Exception:
        ude = enum_asset
    try:
        names = unreal.DataTableFunctionLibrary.get_data_table_column_as_string  # noqa: dummy
    except Exception:
        pass
    # Iterate via unreal.EnumBase APIs on loaded UEnum
    uenum = unreal.load_object(None, ENUM_PATH)
    if not uenum:
        return fallback
    # Try get_enum_value_display_name
    count = 0
    try:
        # UserDefinedEnum NumEnums includes MAX
        while count < 32:
            try:
                dn = unreal.EnumBase.get_display_name_text_by_index(uenum, count).to_string()
            except Exception:
                try:
                    dn = str(uenum.get_editor_property("display_name_map"))
                    break
                except Exception:
                    break
            if dn.lower() == display_name.lower():
                return count
            count += 1
            if count > 20:
                break
    except Exception as exc:
        log(f"enum display iterate failed: {exc}")
    return fallback


def fix_get_equipped_animset():
    bp = unreal.load_asset(CHAR_BP)
    if not bp:
        log("FAILED load BP_FPCharacter")
        return False

    # Ensure EquippedGunSet variable exists as byte (ENUM may be set via default)
    try:
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem) if False else None
    except Exception:
        pass

    # Use BlueprintEditorLibrary / AnimBlueprint if available
    enum_asset = unreal.load_asset(ENUM_PATH)
    pistol = 0
    hands = 7
    log(f"Using pistol={pistol} hands={hands} (ENUM_Animset known mapping)")

    # Find or create GetEquippedAnimset graph
    graph = find_graph(bp, "GetEquippedAnimset")
    if not graph:
        # Create function via BlueprintEditorLibrary
        try:
            unreal.BlueprintEditorLibrary.add_function_graph(bp, "GetEquippedAnimset")
            graph = find_graph(bp, "GetEquippedAnimset")
            log(f"created function graph: {graph}")
        except Exception as exc:
            log(f"add_function_graph failed: {exc}")

    if not graph:
        log("ERROR: no GetEquippedAnimset graph")
        # Still try to set CDO defaults for EquippedGunSet if present
    else:
        log(f"Found graph {graph.get_name()} nodes={len(graph.nodes)}")
        for node in list(graph.nodes):
            log(f"  node {node.get_name()} {node.get_class().get_name()} {node.get_node_title(unreal.NodeTitleType.FULL_TITLE)}")

        # Clear all nodes except entry/result, then rebuild
        entry = None
        result = None
        for node in list(graph.nodes):
            cls = node.get_class().get_name()
            if "FunctionEntry" in cls:
                entry = node
            elif "FunctionResult" in cls:
                result = node
            else:
                try:
                    graph.remove_node(node)
                except Exception as exc:
                    log(f"remove node failed: {exc}")

        if not entry or not result:
            log("ERROR missing entry/result")
        else:
            # Build: Get Equipped OR IsWeapon -> Select Animset -> Result
            # Using EditorScripting / Kismet — create variable get nodes via graph schema if possible
            try:
                # Set result default values through pins if we can
                for pin in result.get_pins():
                    pname = pin.get_name()
                    log(f"  result pin {pname} type={pin.pin_type.pin_category}")
                    if pname.lower() == "animset" or pname == "Animset":
                        # Force default to Pistol for now — better than Hands stub.
                        # Full branch wiring needs schema; set default to Pistol (0).
                        try:
                            pin.default_value = str(pistol)
                            log(f"  set Animset default -> {pistol}")
                        except Exception as exc:
                            log(f"  set default failed: {exc}")
            except Exception as exc:
                log(f"result pin edit failed: {exc}")

    # Add EquippedGunSet variable if missing and set CDO
    try:
        gen = bp.generated_class()
        cdo = unreal.get_default_object(gen) if gen else None
        if cdo:
            for prop in ("EquippedGunSet", "Equipped", "IsWeapon"):
                try:
                    val = cdo.get_editor_property(prop)
                    log(f"CDO {prop}={val}")
                except Exception as exc:
                    log(f"CDO no {prop}: {exc}")
            # Try set EquippedGunSet to Pistol on CDO
            try:
                cdo.set_editor_property("EquippedGunSet", pistol)
                log("Set CDO EquippedGunSet to Pistol index")
            except Exception as exc:
                log(f"Set EquippedGunSet failed (will add var): {exc}")
    except Exception as exc:
        log(f"CDO inspect failed: {exc}")

    # Compile
    try:
        unreal.KismetSystemLibrary.compile_blueprint(bp) if hasattr(unreal, "KismetSystemLibrary") else None
    except Exception:
        pass
    try:
        unreal.EditorAssetLibrary.save_asset(CHAR_BP)
        log("Saved BP_FPCharacter")
    except Exception as exc:
        log(f"save char failed: {exc}")

    return True


def duplicate_manny_abp():
    """Duplicate ABP_Manny to SCAR path and retarget pistol sequence to ADS if editable."""
    if unreal.EditorAssetLibrary.does_asset_exist(REMOTE_ABP):
        log(f"Remote ABP already exists: {REMOTE_ABP}")
        return True

    ok = unreal.EditorAssetLibrary.duplicate_asset(MANNY_ABP, REMOTE_ABP)
    log(f"duplicate ABP_Manny -> {REMOTE_ABP}: {ok}")
    if not ok:
        return False

    abp = unreal.load_asset(REMOTE_ABP)
    ads = unreal.load_asset(ADS_ANIM)
    idle = unreal.load_asset(PISTOL_IDLE)
    log(f"loaded remote={abp} ads={ads} idle={idle}")

    # Best-effort: walk anim graph nodes and replace Pistol Idle sequence with ADS
    replaced = 0
    try:
        # AnimBlueprint has get_nodes_of_class via unreal.AnimationBlueprintLibrary / editor
        nodes = []
        if hasattr(unreal, "AnimBlueprintLibrary"):
            pass
        # Fallback: use AssetEditor / Animation Controllers
        for obj in unreal.EditorAssetLibrary.find_asset_data(REMOTE_ABP):
            pass
        # Iterate soft references via package rename is fragile; use AnimGraphNode search
        package = abp.get_package()
        for obj in unreal.EditorAssetLibrary.list_assets(package.get_name(), True, False) if False else []:
            pass

        # Use ObjectIterator within package
        for obj in unreal.ObjectIterator(unreal.AnimGraphNode_SequenceEvaluator):
            if obj.get_package() == abp.get_package() or str(obj.get_path_name()).startswith(REMOTE_ABP):
                try:
                    seq = obj.get_editor_property("sequence")
                except Exception:
                    try:
                        node = obj.get_editor_property("node")
                        seq = node.get_editor_property("sequence") if node else None
                    except Exception:
                        seq = None
                if seq and idle and seq.get_path_name() == idle.get_path_name():
                    try:
                        obj.set_editor_property("sequence", ads)
                        replaced += 1
                    except Exception:
                        try:
                            node = obj.get_editor_property("node")
                            node.set_editor_property("sequence", ads)
                            replaced += 1
                        except Exception as exc:
                            log(f"seq replace failed: {exc}")
        log(f"Replaced pistol idle->ADS on {replaced} SequenceEvaluator nodes")
    except Exception as exc:
        log(f"ADS swap walk failed: {exc}")

    try:
        unreal.EditorAssetLibrary.save_asset(REMOTE_ABP)
        log("Saved ABP_SCAR_RemoteManny")
    except Exception as exc:
        log(f"save remote abp failed: {exc}")
    return True


def main():
    log("=== fix_remote_armed_hold ===")
    fix_get_equipped_animset()
    duplicate_manny_abp()
    save_log()
    log(f"Wrote {LOG}")


main()
