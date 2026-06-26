import unreal
from pathlib import Path
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
lines = []
for p in ("ScopeSightMesh", "OpticSightMesh", "AimDistanceFromCamera"):
    v = cdo.get_editor_property(p)
    lines.append(f"{p}={v.get_path_name() if hasattr(v,'get_path_name') else v}")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
lines.append(f"EventGraph nodes={len(eg.list_all_nodes())}")
for n in eg.list_all_nodes():
    if "SetStaticMesh" in str(n.get_node_title()):
        lines.append(f"  {n.get_name()} | {n.get_node_title()}")
Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_sniper_post_reset.log").write_text("\n".join(lines))
