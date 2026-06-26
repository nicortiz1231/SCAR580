"""Find attachment application on weapon spawn/equip."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_attachment_apply.log")
lines = []

bp_paths = (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
)

for bp_path in bp_paths:
    bp = unreal.load_asset(bp_path)
    if not bp:
        continue
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(
                k in title
                for k in (
                    "Attachment", "Sight", "Scope", "SetAmmo", "Optic",
                    "ChangeSight", "ItemData", "Item Data",
                )
            ):
                lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")

# Spawn chain after VariableSet_19
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
event_graph = unreal.BlueprintEditorLibrary.find_event_graph(char)
editor = unreal.BlueprintGraphEditor.get_graph_editor(event_graph)

for name in (
    "K2Node_VariableSet_19",
    "K2Node_VariableSet_15",
    "K2Node_SpawnActorFromClass_3",
    "K2Node_SpawnActorFromClass_1",
    "K2Node_BreakStruct_1",
    "K2Node_CallFunction_212",
):
    for node in editor.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
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
            if linked:
                lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
