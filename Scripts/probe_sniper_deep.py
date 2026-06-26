"""Deep probe sniper weapon: attachments, ADS, components, pickup defaults."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_deep.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


def dump_cdo(path: str, label: str) -> None:
    asset = unreal.load_asset(path)
    if not asset:
        log(f"MISSING {path}")
        return
    cdo = unreal.get_default_object(asset.generated_class())
    log(f"=== {label} ===")
    for name in sorted(dir(cdo)):
        if name.startswith("_"):
            continue
        try:
            val = cdo.get_editor_property(name)
        except Exception:
            continue
        if val is None or val == "" or val is False:
            continue
        lower = name.lower()
        if not any(
            k in lower
            for k in (
                "attach", "sight", "scope", "aim", "ads", "fov", "camera",
                "item", "ammo", "mesh", "weapon", "socket", "offset", "distance",
            )
        ):
            continue
        if hasattr(val, "get_path_name"):
            log(f"  {name}={val.get_path_name()}")
        elif isinstance(val, (int, float, str, bool)):
            log(f"  {name}={val!r}")
        else:
            log(f"  {name}={val!r}")


def dump_subobjects(path: str, label: str) -> None:
    bp = unreal.load_asset(path)
    if not bp:
        return
    log(f"=== {label} subobjects ===")
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj:
            continue
        name = obj.get_name()
        cls = obj.get_class().get_name()
        if any(k in name.lower() or k in cls.lower() for k in ("mesh", "scope", "sight", "attach", "weapon")):
            log(f"  {name} | {cls}")
            for prop in sorted(dir(obj)):
                if prop.startswith("_"):
                    continue
                lower = prop.lower()
                if any(k in lower for k in ("mesh", "attach", "sight", "scope", "socket", "static")):
                    try:
                        val = obj.get_editor_property(prop)
                        if val is not None and val != "" and val is not False:
                            if hasattr(val, "get_path_name"):
                                log(f"    {prop}={val.get_path_name()}")
                            else:
                                log(f"    {prop}={val!r}")
                    except Exception:
                        pass


for path, label in (
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper", "BP_Weapon_Sniper"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper", "BP_Weapon_Pickup_Sniper"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle", "BP_Weapon_AmericanRifle"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_Pickup_AmericanRifle.BP_Weapon_Pickup_AmericanRifle", "BP_Weapon_Pickup_AmericanRifle"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol", "BP_Weapon_Pistol"),
):
    dump_cdo(path, label)
    dump_subobjects(path, label)

# ENUM_Sights values
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights",
    "/Game/BodycamFPSKIT/Blueprints/ENUM_Sights",
):
    enum_asset = unreal.load_asset(path)
    if not enum_asset:
        continue
    log(f"=== ENUM_Sights from {path} ===")
    try:
        gen = enum_asset.generated_class() if hasattr(enum_asset, "generated_class") else enum_asset
        for name in sorted(dir(gen)):
            if name.isupper() or name.startswith("NEW"):
                try:
                    log(f"  {name}={getattr(gen, name)!r}")
                except Exception:
                    pass
    except Exception as exc:
        log(f"  ERR {exc}")

# HandsSlot construct attachment defaults
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        log("=== HandsSlot construct attachments ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if "Attach" in pname or "Ammo" in pname or "WeaponData" in pname:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                log(f"  {pname}={val!r}")

OUT.write_text("\n".join(lines))
