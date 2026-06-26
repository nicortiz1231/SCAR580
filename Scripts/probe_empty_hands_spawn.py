"""Probe EmptyHands spawn and swap validation in EventGraph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_empty_hands_spawn.log")
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


def walk_back(editor, start_name: str, depth: int = 0, max_depth: int = 15) -> None:
    for node in editor.list_all_nodes():
        if node.get_name() != start_name:
            continue
        title = str(node.get_node_title()).replace("\n", " | ")
        log(f"{'  '*depth}NODE {start_name} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                continue
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pname == "execute":
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    walk_back(editor, owner.get_name(), depth + 1, max_depth)
        return


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

log("=== Spawn EmptyHands backward chain ===")
walk_back(editor, "K2Node_SpawnActorFromClass_1")

for name in (
    "K2Node_SpawnActorFromClass_1",
    "K2Node_SpawnActorFromClass_2",
    "K2Node_PromotableOperator_4",
    "K2Node_SwitchEnum_0",
    "K2Node_VariableSet_20",
    "K2Node_VariableSet_21",
    "K2Node_VariableSet_23",
    "K2Node_IfThenElse_35",
    "K2Node_MacroInstance_9",
    "K2Node_CallFunction_136",
    "K2Node_VariableSet_47",
    "K2Node_VariableGet_9",
    "K2Node_VariableGet_77",
):
    dump_node(editor, name)

# Find macro Check Before Swap graph if possible
for node in editor.list_all_nodes():
    if node.get_name() == "K2Node_MacroInstance_9":
        try:
            macro = node.get_editor_property("macro_graph")
            if macro:
                log(f"MACRO {macro.get_name()}")
        except Exception as exc:
            log(f"MACRO ERR {exc}")

# All SpawnActor nodes
for node in editor.list_all_nodes():
    if node.get_class().get_name() != "K2Node_SpawnActorFromClass":
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    log(f"SPAWN {node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pname == "Class":
            try:
                log(f"  Class={unreal.BlueprintGraphPinLibrary.get_pin_value(pin)!r}")
            except Exception:
                pass

# BeginPlay -> does it call BeginSetup?
begin = editor.find_event_node("ReceiveBeginPlay")
if begin:
    log("=== BeginPlay forward (shallow) ===")
    stack = [(begin.find_then_pin(), 0)]
    while stack:
        pin, depth = stack.pop()
        if not pin or depth > 8:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            owner = lp.get_owning_node()
            title = str(owner.get_node_title()).replace("\n", " | ")
            log(f"{'  '*depth}{owner.get_name()} | {title}")
            if hasattr(owner, "find_then_pin"):
                stack.append((owner.find_then_pin(), depth + 1))

OUT.write_text("\n".join(lines))
