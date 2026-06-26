"""Probe weapon slots, enum, mouse wheel cycle, and sniper setup."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_slot.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())

ew = cdo.get_editor_property("EquippedWeapon")
enum_cls = type(ew)
log("ENUM_ItemSlots:")
for name in sorted(dir(enum_cls)):
    if name.isupper() or name.startswith("NEW"):
        try:
            log(f"  {name}={int(getattr(enum_cls, name))}")
        except Exception:
            pass

for prop in (
    "EquippedWeapon",
    "SelectedWeapon",
    "MaxMouseWheelTurn",
    "CanSwapWeapon",
    "PrimarySlot",
    "SecondarySlot",
    "MeleeSlot",
    "ThrowableSlot",
    "HandsSlot",
    "SniperSlot",
):
    try:
        val = cdo.get_editor_property(prop)
        if val is None:
            log(f"CDO {prop}=None")
        elif hasattr(val, "get_class"):
            log(f"CDO {prop} class={val.get_class().get_name()}")
            for sub in ("WeaponName", "ItemName", "DisplayName", "AmmoCount"):
                try:
                    log(f"  {sub}={val.get_editor_property(sub)!r}")
                except Exception:
                    pass
        else:
            log(f"CDO {prop}={val!r}")
    except Exception as exc:
        log(f"CDO {prop} ERR {exc}")

subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
log("Blueprint subobjects:")
for handle in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    name = obj.get_name()
    cls = obj.get_class().get_name()
    if any(k in name.lower() or k in cls.lower() for k in ("slot", "weapon", "sniper", "item")):
        log(f"  {name} | {cls}")
        for sub in ("WeaponName", "ItemName", "DisplayName"):
            try:
                log(f"    {sub}={obj.get_editor_property(sub)!r}")
            except Exception:
                pass

event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k in title for k in ("SelectedWeapon", "MaxMouseWheel", "NextWeapon", "CallFunction_170", "CallFunction_302")):
        log(f"NODE {node.get_name()} | {title}")

for name in ("K2Node_CallFunction_170", "K2Node_CallFunction_302", "K2Node_VariableSet_58", "K2Node_IfThenElse_19"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        log(f"=== {name} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            dir_s = "IN" if direction == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
            default = ""
            try:
                default = f" default={pin.get_default_as_string()!r}"
            except Exception:
                pass
            log(f"  {dir_s} {pname}{default} -> {linked}")

# Sniper weapon class
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper",
):
    asset = unreal.load_asset(path)
    log(f"ASSET {path} -> {asset}")

OUT.write_text("\n".join(lines))
