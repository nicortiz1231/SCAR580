"""List sight-related properties on item and sniper classes."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_props.log")
lines = []

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"=== {path.split('/')[-1]} ===")
    for name in sorted(dir(cdo)):
        if name.startswith("_"):
            continue
        if not any(k in name for k in ("Sight", "Scope", "Optic", "Mesh", "Attach")):
            continue
        try:
            val = cdo.get_editor_property(name)
            if hasattr(val, "get_name"):
                lines.append(f"  {name}={val.get_name()}")
            else:
                lines.append(f"  {name}={val!r}")
        except Exception:
            pass

    item_editor = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    for member in sorted(dir(cdo)):
        if "Sight" not in member and "Mesh" not in member:
            continue
        try:
            node = item_editor.add_get_member_variable_node(member)
            lines.append(f"  member_get {member} -> {node.get_name() if node else None}")
            if node:
                item_editor.remove_nodes([node])
        except Exception as exc:
            lines.append(f"  member_get {member} ERR {exc}")

OUT.write_text("\n".join(lines))
