"""Find SelectedWeapon index -> NextWeapon enum mapping."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_wheel_index_map.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

# Find nodes connected from SelectedWeapon getters used in wheel path
targets = set()
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SelectedWeapon" in title and node.get_class().get_name() == "K2Node_VariableGet":
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                targets.add(owner.get_name())

for node in editor.list_all_nodes():
    name = node.get_name()
    if name not in targets and name not in (
        "K2Node_CallFunction_303",
        "K2Node_CallFunction_620",
        "K2Node_CallFunction_107",
        "K2Node_VariableGet_160",
        "K2Node_VariableSet_56",
        "K2Node_VariableSet_64",
        "K2Node_CustomEvent_13",
        "K2Node_MacroInstance_9",
    ):
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
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

# Data table or array for weapon wheel?
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k in title for k in ("Data Table", "Get Data Table", "Array", "WeaponWheel", "ItemSlots")):
        log(f"DATA {node.get_name()} | {title}")

# CDO: search all properties containing weapon/slot/spawn
cdo = unreal.get_default_object(bp.generated_class())
log("CDO properties with weapon/slot:")
for name in dir(cdo):
    lower = name.lower()
    if any(k in lower for k in ("weapon", "slot", "spawn", "pickup", "loadout", "wheel", "sniper")):
        try:
            val = cdo.get_editor_property(name)
            if val is not None and val != "" and val is not False:
                if hasattr(val, "get_path_name"):
                    log(f"  {name}={val.get_path_name()}")
                else:
                    log(f"  {name}={val!r}")
        except Exception:
            pass

# Subobject weapon slot instances on CDO
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    cls = obj.get_class().get_name()
    if "Item" in cls or "Weapon" in cls or "Slot" in obj.get_name():
        log(f"SUBOBJ {obj.get_name()} | {cls}")
        for prop in ("WeaponPickupRef", "ItemType", "ItemSlot", "WeaponType", "ENUM_ItemSlots"):
            try:
                log(f"  {prop}={obj.get_editor_property(prop)!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
