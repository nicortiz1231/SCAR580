"""Full BP_Laser EventGraph dump."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_laser_eventgraph.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Laser/Blueprints/BP_Laser.BP_Laser")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for node in ed.list_all_nodes():
    lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        default = ""
        try:
            default = pin.get_default_value()
        except Exception:
            pass
        conns = []
        for cpin in pin.list_connected_pins():
            cn = cpin.get_owning_node()
            conns.append(f"{cn.get_name()}({str(cn.get_node_title()).replace(chr(10),' ')})")
        if conns or default:
            lines.append(f"  {pname}={default!r} -> {conns}")

OUT.write_text("\n".join(lines))
