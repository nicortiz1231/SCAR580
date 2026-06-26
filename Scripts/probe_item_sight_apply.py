"""Find sight enum -> mesh selection in item base event graph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_item_sight_apply.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(item)
)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    cls = node.get_class().get_name()
    if any(k in title for k in ("ScopeSight", "OpticSight", "SetStaticMesh", "ENUM_Sights", "SpawnAttachment")):
        lines.append(f"{node.get_name()} | {cls} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("self", "NewMesh", "Selection", "Condition", "False", "True", "execute", "then"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    o = lp.get_owning_node()
                    linked.append(f"{o.get_name()}:{pn}")
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val:
                        linked.append(val)
                except Exception:
                    pass
                if linked:
                    lines.append(f"  {pn} -> {linked}")

# sniper beginplay mesh source
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
for prop in ("ScopeSightMesh", "OpticSightMesh"):
    mesh = cdo.get_editor_property(prop)
    lines.append(f"sniper.{prop}={mesh.get_path_name() if mesh else None}")

OUT.write_text("\n".join(lines))
