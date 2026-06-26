"""Diagnose scope ADS: aim chain, near clip, shader params, scope spawn."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_scope_ads_state.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

# AIMOn exec chain
for start in ("K2Node_CallFunction_56", "K2Node_CustomEvent_16"):
    for node in eg.list_all_nodes():
        if node.get_name() != start:
            continue
        lines.append(f"\n=== Forward from {start} ===")
        pin = node.find_output_pin("then")
        if not pin:
            continue
        seen = set()

        def walk(exec_pin, depth=0):
            if not exec_pin or depth > 12:
                return
            n = exec_pin.get_owning_node()
            nid = n.get_name()
            if nid in seen:
                return
            seen.add(nid)
            title = str(n.get_node_title()).replace("\n", " | ")
            lines.append(f"{'  '*depth}{nid} | {title[:70]}")
            then = n.find_output_pin("then")
            if then:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                    if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                        walk(lp, depth + 1)

        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            walk(lp, 0)

# Near clip nodes
lines.append("\n=== Near clip wiring ===")
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SetNearClipPlane" in title or "ExecuteConsoleCommand" in title:
        lines.append(f"{node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                lines.append(f"  {pn}={val}")

# Select_5 FOV
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_Select_5":
        continue
    lines.append("\n=== Select_5 sniper FOV ===")
    pin = node.find_input_pin("NewEnumerator14")
    if pin:
        lines.append(f"  NewEnumerator14={unreal.BlueprintGraphPinLibrary.get_pin_value(pin)}")

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("\n=== Sniper CDO ===")
for prop in (
    "AimDistanceFromCamera",
    "ScopeMat_SightDistance",
    "ScopeMat_GradientParam",
    "ScopeRenderRadius",
    "ChangeSightSpeed",
):
    lines.append(f"  {prop}={cdo.get_editor_property(prop)!r}")

# ScopeRef Aim call nodes
for name in ("K2Node_CallFunction_128", "K2Node_CallFunction_144"):
    for node in eg.list_all_nodes():
        if node.get_name() != name:
            continue
        lines.append(f"\n=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or linked or pn in ("execute", "then", "self", "On/Off"):
                lines.append(f"  {pn} val={val!r} linked={linked}")

OUT.write_text("\n".join(lines))
