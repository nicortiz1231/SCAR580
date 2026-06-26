"""Probe UserConstructionScript and SetWeaponAmmoData on item base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ucs_attach.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for gname in ("UserConstructionScript", "SetWeaponAmmoData"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(item):
        if g.get_name() != gname:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"=== {gname} ===")
        for node in editor.list_all_nodes():
            lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

# VariableGet_20 on character
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)
for node in editor.list_all_nodes():
    if node.get_name() == "K2Node_VariableGet_20":
        lines.append(f"=== VariableGet_20 | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                linked.append(f"{owner.get_name()}:{pname}")
            lines.append(f"  {pname} -> {linked}")

OUT.write_text("\n".join(lines))
