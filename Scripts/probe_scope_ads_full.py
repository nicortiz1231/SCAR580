"""Probe scope material params, IfThenElse_17 branch, and ADS sight path."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_ads_full.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if any(k in title for k in ("ScopeMat", "SightDistance", "GradientParam", "SetScalar", "Material", "PointToShoot")):
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or linked or "Scope" in pn or "Sight" in pn or "Gradient" in pn:
                lines.append(f"  {pn} val={val!r} linked={linked}")

lines.append("\n=== IfThenElse_17 branch ===")
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_IfThenElse_17":
        continue
    for pin_name in ("then", "else"):
        pin = node.find_output_pin(pin_name)
        if not pin:
            continue
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            lines.append(f"  {pin_name} -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")

# Select_5 current FOV values
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_Select_5":
        continue
    lines.append("\n=== Select_5 FOV map ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if val and pn.startswith("NewEnumerator"):
            lines.append(f"  {pn}={val}")

# sniper + rifle scope params
for path, label in (
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper", "sniper"),
    ("/Game/BodycamFPSKIT/Blueprints/Interactables/AmericanRifle/BP_Weapon_AmericanRifle", "rifle"),
):
    bp = unreal.load_asset(f"{path}.BP_Weapon_Sniper" if "Sniper" in path else f"{path}.BP_Weapon_AmericanRifle")
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"\n=== {label} ===")
    for prop in ("AimDistanceFromCamera", "ScopeMat_SightDistance", "ScopeMat_GradientParam", "ChangeSightSpeed"):
        lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")

# AutomaticBase NewEnumerator7 mesh path
auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
if auto:
    for g in unreal.BlueprintEditorLibrary.list_graphs(auto):
        if g.get_name() != "EventGraph":
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            if node.get_name() != "K2Node_SwitchEnum_1":
                continue
            lines.append("\n=== AutomaticBase sight switch ===")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                if pn.startswith("NewEnumerator7"):
                    linked = [str(lp.get_owning_node().get_node_title()).replace("\n"," ")[:40] for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                    lines.append(f"  {pn} -> {linked}")

OUT.write_text("\n".join(lines))
