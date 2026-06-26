"""Dump FOV function graph and enum mapping."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fov_function.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    gname = g.get_name()
    if gname not in ("FOV", "TM_FOV"):
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== Graph {gname} ({len(ed.list_all_nodes())} nodes) ===")
    for node in ed.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        lines.append(f"  {node.get_name()} | {title}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val or pn.startswith("NewEnumerator") or pn in ("Index", "ReturnValue", "TargetFOV", "InFieldOfView"):
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                lines.append(f"    {pn} val={val!r} linked={linked}")

# All Select nodes with FOV values in event graph
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
for node in eg.list_all_nodes():
    if "Select" not in node.get_class().get_name():
        continue
    has_fov_val = False
    pin_dump = []
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if val and any(c.isdigit() for c in val):
            has_fov_val = True
        if val or pn.startswith("NewEnumerator"):
            pin_dump.append(f"    {pn}={val!r}")
    if has_fov_val:
        lines.append(f"\n=== {node.get_name()} | Select ===")
        lines.extend(pin_dump)

# ENUM_Fov asset
enum_asset = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Fov.ENUM_Fov")
lines.append(f"\nENUM_Fov={enum_asset}")

OUT.write_text("\n".join(lines))
