"""Probe all weapon slot input actions and mouse wheel cycle logic."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_all_weapon_slots.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    if cls == "K2Node_EnhancedInputAction" and "Slot" in title:
        log(f"EIA {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname in ("Triggered", "Started"):
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    log(f"  {pname} -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10), ' | ')}")

    if cls == "K2Node_EnhancedInputAction" and "MouseWheel" in title:
        log(f"WHEEL {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname == "ActionValue":
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    log(f"  ActionValue -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10), ' | ')}")

for node in editor.list_all_nodes():
    if node.get_name() in ("K2Node_MacroInstance_77", "K2Node_MacroInstance_9", "K2Node_SwitchEnum_0"):
        log(f"=== {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            dir_s = "IN" if direction == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT"
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
            log(f"  {dir_s} {pname} -> {linked}")

cdo = unreal.get_default_object(bp.generated_class())
ew = cdo.get_editor_property("EquippedWeapon")
enum_cls = type(ew)
log("ENUM members:")
for name in sorted(dir(enum_cls)):
    if name.isupper() or name.startswith("NEW"):
        try:
            log(f"  {name}={int(getattr(enum_cls, name))}")
        except Exception:
            pass

for prop in ("MaxMouseWheelTurn", "CanSwapWeapon"):
    try:
        log(f"CDO {prop}={cdo.get_editor_property(prop)!r}")
    except Exception as exc:
        log(f"CDO {prop} ERR {exc}")

for path in unreal.EditorAssetLibrary.list_assets("/Game/BodycamFPSKIT/Input/Actions", recursive=False):
    if "IA_" in path and "Slot" in path:
        log(f"IA: {path}")

OUT.write_text("\n".join(lines))
