"""Probe ENUM_ItemSlots values and weapon slot checks."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_slots.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


# Try loading enum via generated class
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())

for prop in ("EquippedWeapon", "NextWeapon"):
    val = cdo.get_editor_property(prop)
    log(f"CDO {prop}={val!r} type={type(val)}")

# List enum members from Python type
ew = cdo.get_editor_property("EquippedWeapon")
enum_cls = type(ew)
log(f"Enum class={enum_cls}")
for name in sorted(dir(enum_cls)):
    if name.isupper() or name.startswith("NEW") or name.startswith("NUM"):
        try:
            log(f"  {name}={getattr(enum_cls, name)!r}")
        except Exception:
            pass

# Inspect slot variable types on CDO
for slot in ("PrimarySlot", "SecondarySlot"):
    val = cdo.get_editor_property(slot)
    log(f"CDO {slot}={val!r}")

event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "EquippedWeapon" in title and node.get_class().get_name() == "K2Node_Equality":
        log(f"EQ {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            d = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
            if d == unreal.EdGraphPinDirection.EGPD_INPUT:
                try:
                    log(f"  IN {pn} default={pin.get_default_as_string()!r}")
                except Exception:
                    log(f"  IN {pn}")
    if node.get_class().get_name() == "K2Node_EnumLiteral":
        log(f"EnumLiteral {node.get_name()} | {title}")

OUT.write_text("\n".join(lines))
