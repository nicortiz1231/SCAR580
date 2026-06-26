"""Trace mouse wheel chain and all HandsSlot/EmptyHands references."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_wheel_chain.log")
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


def walk_exec(editor, start_name: str, depth: int = 0, max_depth: int = 20) -> None:
    for node in editor.list_all_nodes():
        if node.get_name() != start_name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        log(f"{'  '*depth}EXEC {start_name} | {title}")
        then = node.find_then_pin() if hasattr(node, "find_then_pin") else None
        pins = [then] if then else []
        if node.get_class().get_name() == "K2Node_ExecutionSequence":
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn.startswith("then_"):
                    pins.append(pin)
        if node.get_class().get_name() == "K2Node_IfThenElse":
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn in ("then", "else"):
                    pins.append(pin)
        for pin in pins:
            if not pin or depth >= max_depth:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                walk_exec(editor, owner.get_name(), depth + 1, max_depth)
        return


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

# All graphs for EmptyHands / HandsSlot / Sniper string refs in pin values
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            try:
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            except Exception:
                val = ""
            if val and any(k in val for k in ("EmptyHands", "Sniper", "HandsSlot")):
                log(
                    f"[{g.get_name()}] {node.get_name()} "
                    f"{unreal.BlueprintGraphPinLibrary.get_pin_name(pin)}={val!r}"
                )

event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

log("=== Mouse wheel exec chain ===")
walk_exec(editor, "K2Node_IfThenElse_16")

for name in (
    "K2Node_IfThenElse_16",
    "K2Node_MacroInstance_77",
    "K2Node_IfThenElse_54",
    "K2Node_VariableSet_55",
    "K2Node_VariableSet_56",
    "K2Node_CastByteToEnum_3",
    "K2Node_CallFunction_303",
    "K2Node_CallFunction_340",
    "K2Node_CallFunction_170",
    "K2Node_VariableSet_45",
    "K2Node_IfThenElse_19",
    "K2Node_VariableSet_36",
    "K2Node_VariableSet_58",
    "K2Node_CustomEvent_13",
    "K2Node_MacroInstance_9",
    "K2Node_VariableSet_140",
    "K2Node_CallFunction_620",
    "K2Node_CallFunction_112",
):
    dump_node(editor, name)

# Enum literals in wheel path
for node in editor.list_all_nodes():
    if node.get_class().get_name() == "K2Node_EnumLiteral":
        title = str(node.get_node_title()).replace("\n", " | ")
        if "ItemSlots" in title or "ItemSlot" in title:
            log(f"ENUM_LIT {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val:
                        log(f"  {pname}={val!r}")
                except Exception:
                    pass

OUT.write_text("\n".join(lines))
