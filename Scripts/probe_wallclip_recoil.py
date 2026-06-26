import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_wallclip_recoil.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for gname in ("Wall Clip", "Recoil", "Fire"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != gname:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"=== {gname} ({len(editor.list_all_nodes())} nodes) ===")
        for node in editor.list_all_nodes()[:25]:
            lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append("=== sniper EventGraph scope nodes ===")
for node in editor.list_all_nodes():
    t = str(node.get_node_title()).replace("\n"," | ")
    if any(k in t for k in ("SpawnAttachment","SetStaticMesh","SetVisibility","CustomEvent")):
        lines.append(f"  {node.get_name()} | {t}")
OUT.write_text("\n".join(lines))
