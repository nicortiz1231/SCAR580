"""Probe valid-path weapon spawn (SpawnActorFromClass_3) and item equip."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawn_valid_path.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


def dump_node(editor, name: str) -> None:
    for node in editor.list_all_nodes():
        if node.get_name() != name:
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
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    default = f" val={val!r}"
            except Exception:
                pass
            log(f"  {dir_s} {pname}{default} -> {linked}")


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for name in (
    "K2Node_SpawnActorFromClass_3",
    "K2Node_CallFunction_212",
    "K2Node_CallFunction_54",
    "K2Node_CallFunction_295",
    "K2Node_MacroInstance_7",
    "K2Node_GetClassDefaults_1",
    "K2Node_VariableGet_45",
    "K2Node_IfThenElse_35",
):
    dump_node(editor, name)

# PromotableOperator_4 inputs
for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_PromotableOperator_4":
        continue
    log("=== PromotableOperator_4 all pins ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            linked.append(f"{owner.get_name()}:{pname}")
        try:
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                linked.append(f"val={val!r}")
        except Exception:
            pass
        log(f"  {pname} -> {linked}")

# DT_Item class
item_cls = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/DT_Item.DT_Item")
if item_cls:
    gen = item_cls.generated_class() if hasattr(item_cls, "generated_class") else item_cls
    log(f"DT_Item class={gen}")

OUT.write_text("\n".join(lines))
