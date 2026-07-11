"""Find end of Construct Sequence then_1 branch."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_then1_tail.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))
seq = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_ExecutionSequence_0")

for pin in unreal.BlueprintEditorLibrary.list_all_pins(seq):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    if pn != "then_1":
        continue
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        start = lp.get_owning_node()
        lines.append(f"then_1 starts at {start.get_name()} | {start.get_node_title()}")
        current = start
        visited = set()
        while current and current.get_name() not in visited:
            visited.add(current.get_name())
            lines.append(f"  {current.get_name()} | {current.get_node_title()}")
            then = current.find_output_pin("then")
            if not then:
                break
            nxt = [
                lp2.get_owning_node()
                for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)
                if lp2.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT
            ]
            if not nxt:
                lines.append(f"  TAIL={current.get_name()}")
                break
            current = nxt[0]

OUT.write_text("\n".join(lines))
