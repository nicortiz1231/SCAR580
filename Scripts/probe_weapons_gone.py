"""Diagnose broken weapon visibility after scope fixes."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapons_gone.log")
lines = []


def walk_exec(editor, start_pin, label, max_depth=20):
    lines.append(f"=== {label} ===")
    if not start_pin:
        lines.append("  (no start pin)")
        return
    stack = [(start_pin, 0)]
    while stack:
        pin, depth = stack.pop()
        if depth > max_depth:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            title = str(o.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{o.get_name()} | {title}")
            nxt = o.find_output_pin("then") if hasattr(o, "find_output_pin") else None
            if nxt:
                stack.append((nxt, depth + 1))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for name in (
    "K2Node_MacroInstance_4",
    "K2Node_CallFunction_140",
    "K2Node_CallFunction_141",
    "K2Node_CallFunction_212",
    "K2Node_CallFunction_234",
    "K2Node_VariableSet_15",
    "K2Node_VariableSet_19",
):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        then = node.find_output_pin("then")
        walk_exec(editor, then, f"forward from {name}")

# orphaned exec inputs on key sets
for name in ("K2Node_VariableSet_0", "K2Node_VariableSet_59", "K2Node_VariableGet_83", "K2Node_VariableGet_133"):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        exec_in = node.find_input_pin("execute")
        linked = []
        if exec_in:
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in):
                linked.append(lp.get_owning_node().get_name())
        lines.append(f"{name} exec_in -> {linked or 'DISCONNECTED'}")

# compile status
try:
    status = unreal.BlueprintEditorLibrary.get_blueprint_compile_status(bp)
    lines.append(f"BP_FPCharacter compile_status={status}")
except Exception as exc:
    lines.append(f"compile_status ERR {exc}")

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
ied = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(item)
)
for node in ied.list_all_nodes():
    if "SpawnAttachments" not in str(node.get_node_title()):
        continue
    then = node.find_output_pin("then")
    walk_exec(ied, then, "item SpawnAttachments")

OUT.write_text("\n".join(lines))
