import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_aimdownsight.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    if g.get_name() != "AimDownSight":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if any(k in pn.lower() for k in ("aim", "distance", "camera", "offset", "fov", "scope")):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    o = lp.get_owning_node()
                    linked.append(o.get_name())
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val:
                        linked.append(val)
                except Exception:
                    pass
                lines.append(f"  {pn} -> {linked}")

# compare aim distances
for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle.BP_Weapon_AmericanRifle",
):
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"{path.split('/')[-1]} AimDistanceFromCamera={cdo.get_editor_property('AimDistanceFromCamera')}")

OUT.write_text("\n".join(lines))
