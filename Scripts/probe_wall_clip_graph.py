import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_wall_clip_graph.log")
lines = []
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if "Wall" not in g.get_name() and g.get_name() != "Recoil":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {g.get_name()} ===")
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n"," | ")
        if any(k in title.lower() for k in ("clip", "near", "camera", "wall", "offset", "push")):
            lines.append(f"  {node.get_name()} | {title}")

# AC_ProceduralAnimation Wall Clip function
ac = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation")
if ac:
    for g in unreal.BlueprintEditorLibrary.list_graphs(ac):
        if "Wall" not in g.get_name() and "Clip" not in g.get_name():
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"=== AC {g.get_name()} ===")
        for node in editor.list_all_nodes()[:30]:
            lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")
OUT.write_text("\n".join(lines))
