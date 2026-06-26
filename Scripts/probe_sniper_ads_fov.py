"""Probe sniper ADS FOV wiring and current values."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_ads_fov.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if not any(k in title for k in ("FOV", "FieldOfView", "SetFieldOfView", "Switch on ENUM_Sights")):
        continue
    lines.append(f"{node.get_name()} | {title}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if val or linked or pn.startswith("NewEnumerator"):
            lines.append(f"  {pn} val={val!r} linked={linked}")

# AimDownSight graph on character
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "AimDownSight":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== AimDownSight ({len(ed.list_all_nodes())} nodes) ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title.lower() for k in ("fov", "sight", "scope", "camera", "aim")):
            lines.append(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val or "fov" in pn.lower():
                    lines.append(f"    {pn}={val!r}")

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("\n=== Sniper scope mat params ===")
for prop in ("ScopeMat_SightDistance", "ScopeMat_GradientParam", "AimDistanceFromCamera"):
    lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")

cdo_char = unreal.get_default_object(char.generated_class())
lines.append(f"\n=== Character FOV_Base={cdo_char.get_editor_property('FOV_Base')!r} ===")

OUT.write_text("\n".join(lines))
