"""Trace character ScopeRef/Aim exec wiring for ADS."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_aim_wire.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

# trace knot 49 network
for knot_name in ("K2Node_Knot_4", "K2Node_Knot_49", "K2Node_Knot_22", "K2Node_Knot_48"):
    for node in eg.list_all_nodes():
        if node.get_name() != knot_name:
            continue
        lines.append(f"\n=== {knot_name} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}|{str(o.get_node_title()).replace(chr(10),' ')[:30]}")
            if linked:
                lines.append(f"  {unreal.BlueprintGraphPinLibrary.get_pin_name(pin)} -> {linked}")

# Find all exec connections to VariableGet_81 and 191
for vname in ("K2Node_VariableGet_81", "K2Node_VariableGet_191"):
    for node in eg.list_all_nodes():
        if node.get_name() != vname:
            continue
        lines.append(f"\n=== Who should exec into {vname}? ===")
        # search all nodes whose then connects to this execute
        for other in eg.list_all_nodes():
            then = other.find_output_pin("then")
            if not then:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                if lp.get_owning_node().get_name() == vname:
                    lines.append(f"  <- {other.get_name()} | {str(other.get_node_title()).replace(chr(10),' | ')}")

# Forward from SwitchEnum_4 all outputs
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_SwitchEnum_4":
        continue
    lines.append("\n=== SwitchEnum_4 all enum exec outputs ===")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not pn.startswith("NewEnumerator"):
            continue
        linked = [f"{lp.get_owning_node().get_name()}|{str(lp.get_owning_node().get_node_title()).replace(chr(10),' ')[:35]}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        lines.append(f"  {pn} -> {linked}")

# Compare with BODYCAMFPSKIT original - file size
import os
for proj, label in (
    ("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Content/BodycamFPSKIT/Blueprints/BP_FPCharacter.uasset", "SCAR"),
    ("/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Content/BodycamFPSKIT/Blueprints/BP_FPCharacter.uasset", "ORIG"),
):
    if os.path.exists(proj):
        lines.append(f"\n{label} BP_FPCharacter size={os.path.getsize(proj)}")

OUT.write_text("\n".join(lines))
