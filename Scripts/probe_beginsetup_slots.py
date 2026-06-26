"""Full BeginSetup graph dump for weapon slots."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_beginsetup_slots.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append("=== BeginSetup ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{node.get_name()} | {title}")
        if node.get_class().get_name() in ("K2Node_VariableSet", "K2Node_CreateObject", "K2Node_GenericCreateObject", "K2Node_SpawnActorFromClass"):
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = lp.get_owning_node()
                    linked.append(f"{owner.get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}")
                default = ""
                try:
                    default = f" default={pin.get_default_as_string()!r}"
                except Exception:
                    pass
                lines.append(f"  IN {pname}{default} -> {linked}")

OUT.write_text("\n".join(lines))
