"""Full SetWeaponAmmoData graph trace."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_setweaponammo_full.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
g = next(g for g in unreal.BlueprintEditorLibrary.list_graphs(item) if g.get_name() == "SetWeaponAmmoData")
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

for node in ed.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{node.get_name()} | {title}")

lines.append("\n=== Exec flow ===")
entry = next(n for n in ed.list_all_nodes() if n.get_class().get_name() == "K2Node_FunctionEntry")
stack = [(entry.find_output_pin("then"), 0)]
while stack:
    pin, depth = stack.pop()
    if not pin:
        continue
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        o = lp.get_owning_node()
        t = str(o.get_node_title()).replace("\n", " | ")
        extra = ""
        if o.get_class().get_name() == "K2Node_IfThenElse":
            cond = o.find_input_pin("Condition")
            if cond:
                for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(cond):
                    extra = f" cond<-{lp2.get_owning_node().get_name()}"
        lines.append(f"{'  '*depth}{o.get_name()} | {t}{extra}")
        for branch in ("then", "else"):
            nxt = o.find_output_pin(branch)
            if nxt:
                stack.append((nxt, depth + 1))

OUT.write_text("\n".join(lines))
