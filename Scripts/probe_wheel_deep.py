"""Deep probe of weapon wheel: SelectedWeapon index -> enum -> slot."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_wheel_deep.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

# ENUM values
enum_asset = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_ItemSlots.ENUM_ItemSlots")
cdo = unreal.get_default_object(bp.generated_class())
ew = cdo.get_editor_property("EquippedWeapon")
enum_cls = type(ew)
log("ENUM_ItemSlots members:")
for name in sorted(dir(enum_cls)):
    if name.isupper() or name.startswith("NEW"):
        try:
            log(f"  {name}={int(getattr(enum_cls, name))}")
        except Exception:
            pass

# CastByteToEnum default pins (index -> enum mapping)
for node in editor.list_all_nodes():
    if node.get_class().get_name() != "K2Node_CastByteToEnum":
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    if "ENUM_ItemSlots" not in title:
        continue
    log(f"=== {node.get_name()} | {title} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname in ("Byte", "ReturnValue", "execute", "then"):
            continue
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                log(f"  {pname}={val!r}")
        except Exception:
            pass

# Mouse wheel input chain
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "MouseWheel" in title or "IA_MouseWheel" in title:
        log(f"WHEEL_NODE {node.get_name()} | {title}")
        then = node.find_then_pin() if hasattr(node, "find_then_pin") else None
        if then:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                owner = lp.get_owning_node()
                log(f"  then -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

# Trace from IA_MouseWheel
for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    if cls == "K2Node_EnhancedInputAction" and "MouseWheel" in title:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                log(f"MW {pname} -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

# BeginSetup HandsSlot construct pin values NOW
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        log("=== BeginSetup HandsSlot construct (current) ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    log(f"  {pname}={val!r}")
            except Exception:
                pass

# Select node enum -> slot mapping
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_Select_0":
        continue
    log("=== K2Node_Select_0 slot mapping ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not pname.startswith("NewEnumerator"):
            continue
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        log(f"  {pname} -> {linked}")

# Equality nodes comparing SelectedWeapon to constants
for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    title = str(node.get_node_title()).replace("\n", " | ")
    if cls == "K2Node_CallFunction" and "Equal (Integer)" in title:
        pins = {}
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname == "A":
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    pins["A"] = str(owner.get_node_title()).replace("\n", " | ")
            elif pname == "B":
                try:
                    pins["B"] = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                except Exception:
                    pass
        if pins.get("A") and "SelectedWeapon" in pins.get("A", ""):
            log(f"EQ SelectedWeapon == {pins.get('B')!r}")

OUT.write_text("\n".join(lines))
