import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_props2.log")
lines = []
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
    lines.append(f"=== {path} ===")
    for prop in ("ScopeSightMesh", "OpticSightMesh", "OpticSight", "ItemData"):
        try:
            val = cdo.get_editor_property(prop)
            lines.append(f"  prop {prop}={val.get_name() if hasattr(val,'get_name') else val!r}")
        except Exception as exc:
            lines.append(f"  prop {prop} ERR {exc}")
        try:
            node = editor.add_get_member_variable_node(prop)
            lines.append(f"  get {prop} -> {node.get_name() if node else None}")
            if node:
                editor.remove_nodes([node])
        except Exception as exc:
            lines.append(f"  get {prop} ERR {exc}")
OUT.write_text("\n".join(lines))
