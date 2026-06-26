"""Map ENUM_Sights values and find sight->mesh assignment."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_enum_mesh.log")
lines = []

# enum asset display names
enum_asset = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Sights")
lines.append(f"enum_asset={enum_asset}")
for prop in dir(enum_asset):
    if prop.startswith("_"):
        continue
    try:
        val = enum_asset.get_editor_property(prop)
        if val is not None:
            lines.append(f"  {prop}={val!r}")
    except Exception:
        pass

# generated NUM_Sights
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
cdo = unreal.get_default_object(item.generated_class())
lines.append("=== NUM_Sights members ===")
for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    try:
        val = cdo.get_editor_property(name)
    except Exception:
        continue
    t = type(val).__name__
    if "Sight" in name or "NUM" in t or "Enumerator" in t:
        lines.append(f"  {name}={val!r}")

# character sight switch branches -> what functions they call
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(bp)
)

for sw_name in ("K2Node_SwitchEnum_3", "K2Node_SwitchEnum_4"):
    for node in editor.list_all_nodes():
        if node.get_name() != sw_name:
            continue
        lines.append(f"=== {sw_name} branches ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if not pn.startswith("NewEnumerator"):
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                title = str(o.get_node_title()).replace("\n", " | ")
                lines.append(f"  {pn} -> {o.get_name()} | {title}")
                # one level deeper for set mesh
                if hasattr(o, "find_then_pin"):
                    nxt = o.find_then_pin()
                    if nxt:
                        for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(nxt):
                            o2 = lp2.get_owning_node()
                            t2 = str(o2.get_node_title()).replace("\n", " | ")
                            lines.append(f"    then -> {o2.get_name()} | {t2}")

# item base: any SetStaticMesh targeting OpticSight
item_editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(item)
)
lines.append("=== item EventGraph sight/mesh nodes ===")
for node in item_editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k in title for k in ("SetStaticMesh", "OpticSight", "ScopeSight", "SpawnAttachment", "Switch on ENUM_Sights")):
        lines.append(f"  {node.get_name()} | {title}")

# pickup sniper sight default
pickup = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"
)
pcdo = unreal.get_default_object(pickup.generated_class())
sight = pcdo.get_editor_property("Item Data AttachmentsSight")
lines.append(f"pickup_sight={sight!r} name={getattr(sight, 'name', '')} value={int(sight) if sight is not None else '?'}")

OUT.write_text("\n".join(lines))
