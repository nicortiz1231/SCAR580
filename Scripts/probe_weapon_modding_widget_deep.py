"""Trace UI_WeaponModding populate + layout nodes."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_modding_widget_deep.log")
lines = []

wbp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Widgets/UI_WeaponModding.UI_WeaponModding")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(wbp))


def walk(node, depth=0, seen=None, max_d=25):
    if seen is None:
        seen = set()
    if depth > max_d or id(node) in seen:
        return
    seen.add(id(node))
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{node.get_name()} | {title}")
    then = node.find_output_pin("then")
    if not then:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        walk(lp.get_owning_node(), depth + 1, seen, max_d)


for ev in ("PreConstruct", "Construct", "Event Pre Construct", "Event Construct"):
    node = None
    for n in eg.list_all_nodes():
        if ev in str(n.get_node_title()):
            node = n
            break
    if node:
        lines.append(f"\n=== chain from {ev} ===")
        walk(node)

lines.append("\n=== ClearOptions / RemoveOption nodes ===")
for node in eg.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "ClearOptions" in title or "RemoveOption" in title or "ClearSelection" in title:
        lines.append(f"  {node.get_name()} | {title}")

lines.append("\n=== ForEach enum loops wiring ===")
for name in (
    "K2Node_ForEachElementInEnum_2",
    "K2Node_ForEachElementInEnum_0",
    "K2Node_ForEachElementInEnum_3",
    "K2Node_ForEachElementInEnum_4",
):
    node = next((n for n in eg.list_all_nodes() if n.get_name() == name), None)
    if not node:
        continue
    lines.append(f"\n--- {name} | {node.get_node_title()} ---")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = [f"{lp.get_owning_node().get_name()}:{str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
        if linked:
            lines.append(f"  {pn} -> {linked}")

# generated widget class components via CDO
cls = wbp.generated_class()
cdo = unreal.get_default_object(cls)
lines.append(f"\n=== widget class {cls.get_name()} ===")
for name in dir(cdo):
    if name.isupper() or name.startswith("_"):
        continue
    if any(k in name.lower() for k in ("sight", "laser", "muzzle", "grip", "combo", "box", "canvas", "scale")):
        try:
            val = cdo.get_editor_property(name)
            lines.append(f"  {name}={val!r}")
        except Exception:
            pass

OUT.write_text("\n".join(lines))
