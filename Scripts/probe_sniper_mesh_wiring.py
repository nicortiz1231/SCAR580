import unreal
from pathlib import Path
OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_mesh_wiring.log")
lines = []
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
editor = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
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
        if linked and pn in ("execute", "then", "self", "NewMesh", "OpticSight", "ScopeSightMesh"):
            lines.append(f"  {pn} -> {linked}")
cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"ScopeSightMesh={cdo.get_editor_property('ScopeSightMesh').get_name()}")
lines.append(f"OpticSightMesh={cdo.get_editor_property('OpticSightMesh').get_name()}")
OUT.write_text("\n".join(lines))
