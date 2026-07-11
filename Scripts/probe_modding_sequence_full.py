"""Full trace of Construct Sequence branches."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_modding_sequence_full.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))


def walk_exec(node, depth=0, seen=None, max_d=40):
    if seen is None:
        seen = set()
    nid = node.get_name()
    if depth > max_d or nid in seen:
        return
    seen.add(nid)
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{nid} | {title}")
    then = node.find_output_pin("then")
    if not then:
        # sequence has then_0, then_1...
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn.startswith("then"):
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                        walk_exec(lp.get_owning_node(), depth + 1, seen, max_d)
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
            walk_exec(lp.get_owning_node(), depth + 1, seen, max_d)


seq = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_ExecutionSequence_0")
lines.append("=== From Sequence ===")
walk_exec(seq)

pre = next(n for n in eg.list_all_nodes() if "PreConstruct" in str(n.get_node_title()))
lines.append("\n=== From PreConstruct ===")
walk_exec(pre)

# count AddOption reachability
lines.append("\n=== PreConstruct execute pin ===")
for pin in unreal.BlueprintEditorLibrary.list_all_pins(pre):
    pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
    if pn == "then":
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            lines.append(f"  -> {lp.get_owning_node().get_name()} | {lp.get_owning_node().get_node_title()}")

OUT.write_text("\n".join(lines))
