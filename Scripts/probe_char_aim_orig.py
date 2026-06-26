"""Compare ScopeRef Aim wiring: SCAR vs original Bodycam."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_char_aim_orig.log")
lines = []

def dump_char(label, project_path):
    unreal.SystemLibrary.execute_console_command(None, f"SwitchProject {project_path}") if False else None
    char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    if not char:
        lines.append(f"{label}: MISSING")
        return
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
    lines.append(f"\n========== {label} ==========")
    for vname in ("K2Node_VariableGet_81", "K2Node_VariableGet_191", "K2Node_CallFunction_128", "K2Node_CallFunction_144"):
        for node in eg.list_all_nodes():
            if node.get_name() != vname:
                continue
            lines.append(f"\n--- {vname} | {str(node.get_node_title()).replace(chr(10),' | ')} ---")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if linked or val:
                    lines.append(f"  {pn} val={val!r} linked={linked}")

# SCAR only in current session
dump_char("SCAR", "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/SCAR.uproject")

OUT.write_text("\n".join(lines))
