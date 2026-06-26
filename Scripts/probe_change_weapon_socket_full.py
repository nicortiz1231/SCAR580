"""Dump ChangeWeaponSocket function graph fully."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_change_weapon_socket_full.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "ChangeWeaponSocket":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== ChangeWeaponSocket ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self", "NewMesh", "ItemData", "Sight", "Selection"):
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if linked or val:
                    lines.append(f"  {pn} -> {linked or val}")

OUT.write_text("\n".join(lines))
