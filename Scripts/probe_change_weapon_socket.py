"""Resolve ChangeWeaponSocket function and trace its graph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_change_weapon_socket.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))

node496 = None
for node in editor.list_all_nodes():
    if node.get_name() == "K2Node_CallFunction_496":
        node496 = node
        break

if node496:
    lines.append(f"496 title={node496.get_node_title()}")
    for prop in ("function_reference", "member_name", "member_parent"):
        try:
            lines.append(f"  {prop}={node496.get_editor_property(prop)}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = g.get_name()
    if "ChangeWeapon" not in gname and "Socket" not in gname:
        continue
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== graph {gname} ===")
    for node in ged.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("ItemData", "SetStaticMesh", "ScopeSight", "OpticSight", "Attachment", "SpawnAttachment")):
            lines.append(f"  {node.get_name()} | {title}")

# search all char graphs for ChangeWeaponSocket entry
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ged.list_all_nodes():
        if "ChangeWeaponSocket" in str(node.get_node_title()):
            lines.append(f"FOUND [{g.get_name()}] {node.get_name()} | {node.get_node_title()}")

OUT.write_text("\n".join(lines))
