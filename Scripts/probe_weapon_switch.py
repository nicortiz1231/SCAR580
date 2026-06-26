"""Probe weapon swap wiring in BP_FPCharacter."""
import json
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_switch.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

TARGETS = {
    "K2Node_CustomEvent_13",
    "K2Node_EnhancedInputAction_10",
    "K2Node_EnhancedInputAction_11",
    "K2Node_EnhancedInputAction_20",
    "K2Node_CallFunction_279",
    "K2Node_CallFunction_248",
    "K2Node_CallFunction_136",
    "K2Node_CallFunction_103",
    "K2Node_CallFunction_39",
    "K2Node_MacroInstance_9",
    "K2Node_SwitchEnum_0",
}

for node in editor.list_all_nodes():
    name = node.get_name()
    if name not in TARGETS:
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    log(f"=== {name} | {title} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pin_name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
        dir_s = "IN" if direction == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        log(f"  {dir_s} {pin_name} -> {linked}")

# CDO defaults
cdo = unreal.get_default_object(bp.generated_class())
for prop in ("EquippedWeapon", "SelectedWeapon", "CanSwapWeapon", "MaxMouseWheelTurn"):
    try:
        log(f"CDO {prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        log(f"CDO {prop} ERR {exc}")

# enum values
try:
    enum_asset = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/ENUM_ItemSlots")
    if enum_asset:
        for name in dir(enum_asset):
            if not name.startswith("_"):
                try:
                    log(f"ENUM_ItemSlots.{name}={getattr(enum_asset, name)}")
                except Exception:
                    pass
except Exception as exc:
    log(f"ENUM load ERR {exc}")

OUT.write_text("\n".join(lines))
