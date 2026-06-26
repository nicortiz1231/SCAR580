"""Resolve FOV enum values used for sniper scope ADS (NewEnumerator14)."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fov_enum.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

FOV_NODES = ("K2Node_CallFunction_193", "K2Node_CallFunction_60", "K2Node_CallFunction_44", "K2Node_CallFunction_43")

for name in FOV_NODES:
    node = None
    for n in eg.list_all_nodes():
        if n.get_name() == name:
            node = n
            break
    if not node:
        continue
    lines.append(f"\n=== {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}|{str(o.get_node_title()).replace(chr(10),' ')[:40]}")
        if val or linked:
            lines.append(f"  {pn} val={val!r} linked={linked}")

# FOV custom event + timeline
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if title in ("FOV", "TM_FOV") or "K2Node_CustomEvent_71" == node.get_name():
        lines.append(f"\n=== {node.get_name()} | {title} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
            if val or linked:
                lines.append(f"  {pn} val={val!r} linked={linked}")

# K2Node_Select_5 feeding TargetFOV
for node in eg.list_all_nodes():
    if "Select" not in node.get_class().get_name():
        continue
    title = str(node.get_node_title())
    if "FOV" not in title and node.get_name() != "K2Node_Select_5":
        continue
    lines.append(f"\n=== {node.get_name()} | {title.replace(chr(10),' | ')} ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if val or linked or pn.startswith("NewEnumerator") or pn == "ReturnValue":
            lines.append(f"  {pn} val={val!r} linked={linked}")

# Search for ENUM_FOV asset
for path in (
    "/Game/BodycamFPSKIT/Blueprints/ENUM_FOV",
    "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_FOV",
    "/Game/BodycamFPSKIT/ENUM_FOV",
):
    asset = unreal.load_asset(path)
    if asset:
        lines.append(f"\nLoaded enum {path}: {asset}")

# dump all graphs named FOV
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if "FOV" not in g.get_name():
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== Graph {g.get_name()} ===")
    for node in ed.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

OUT.write_text("\n".join(lines))
