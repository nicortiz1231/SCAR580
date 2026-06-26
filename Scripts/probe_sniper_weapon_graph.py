"""Probe BP_Weapon_Sniper and BP_Item_Base for attachment/ADS setup."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_weapon_graph.log")
lines = []


def dump_graph(bp_path: str, graph_names=None) -> None:
    bp = unreal.load_asset(bp_path)
    if not bp:
        return
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if graph_names and g.get_name() not in graph_names:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"### {bp_path.split('/')[-1]} [{g.get_name()}]")
        for node in editor.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(
                k in title
                for k in (
                    "SpawnAttachment", "Sight", "Scope", "AimDown", "BeginPlay",
                    "SetAmmo", "ItemData", "Attachment", "Optic", "Iron",
                )
            ):
                lines.append(f"  {node.get_name()} | {title}")


dump_graph("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
dump_graph("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")

# Item base CDO ItemData default
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
cdo = unreal.get_default_object(item.generated_class())
for prop in ("ItemData", "Item Data", "Attachments"):
    try:
        lines.append(f"ItemBase {prop}={cdo.get_editor_property(prop)!r}")
    except Exception:
        pass

# Sniper CDO all props with values
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
scdo = unreal.get_default_object(sniper.generated_class())
lines.append("### Sniper CDO")
for name in sorted(dir(scdo)):
    if name.startswith("_"):
        continue
    try:
        val = scdo.get_editor_property(name)
    except Exception:
        continue
    if val is None or val == "" or val is False:
        continue
    if isinstance(val, float) and val in (0.0, 1.0):
        continue
    if isinstance(val, int) and val == 0:
        continue
    if hasattr(val, "get_path_name"):
        lines.append(f"  {name}={val.get_path_name()}")
    elif isinstance(val, (int, float, str, bool)):
        lines.append(f"  {name}={val!r}")

OUT.write_text("\n".join(lines))
