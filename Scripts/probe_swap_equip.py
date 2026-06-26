"""Trace BeginSetup usage, swap equip chain, and EmptyHands comparisons."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_swap_equip.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "BeginSetup" in title or title == "BeginSetup":
            log(f"[{g.get_name()}] {node.get_name()} | {title}")
        if node.get_class().get_name() == "K2Node_MacroInstance":
            if "BeginSetup" in title or "Setup" in title:
                log(f"MACRO [{g.get_name()}] {node.get_name()} | {title}")
        if node.get_class().get_name() == "K2Node_CallFunction":
            for prop in ("function_reference",):
                try:
                    ref = str(node.get_editor_property(prop))
                    if "BeginSetup" in ref:
                        log(f"CALL [{g.get_name()}] {node.get_name()} | {ref}")
                except Exception:
                    pass

event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

# Who uses PromotableOperator_4 result?
for node in editor.list_all_nodes():
    if node.get_name() == "K2Node_PromotableOperator_4":
        log("=== PromotableOperator_4 outputs ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_OUTPUT:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                log(f"  -> {owner.get_name()} | {str(owner.get_node_title()).replace(chr(10),' | ')}")

# Forward from SpawnActorFromClass_1
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_VariableSet_15":
        continue
    log("=== VariableSet_15 (after EmptyHands spawn) ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                linked.append(f"val={val!r}")
        except Exception:
            pass
        log(f"  {pname} -> {linked}")

# MacroInstance_4 full context
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_MacroInstance_4":
        continue
    log("=== MacroInstance_4 Is Valid ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
        log(f"  {pname} -> {linked}")

# Find all references to HandsSlot set
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if "Set HandsSlot" in title:
            log(f"SET_HANDS [{g.get_name()}] {node.get_name()}")

# Sniper pickup - default item data for construct
pickup = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"
)
if pickup:
    cdo = unreal.get_default_object(pickup.generated_class())
    for prop in dir(cdo):
        if "item" in prop.lower() or "ammo" in prop.lower():
            try:
                val = cdo.get_editor_property(prop)
                if val is not None and val != "" and val is not False:
                    log(f"pickup.{prop}={val!r}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
