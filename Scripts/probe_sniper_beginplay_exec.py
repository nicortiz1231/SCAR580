import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_beginplay_exec.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(sniper)
)
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn not in ("execute", "then"):
            continue
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(o.get_name())
        if linked:
            lines.append(f"  {pn} -> {linked}")

cdo = unreal.get_default_object(sniper.generated_class())
lines.append(f"AimDistanceFromCamera={cdo.get_editor_property('AimDistanceFromCamera')}")

OUT.write_text("\n".join(lines))
