import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_custom_event3.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(item)
)

for node in editor.list_all_nodes():
    if node.get_name() != "K2Node_CustomEvent_3":
        continue
    lines.append(f"class={node.get_class().get_name()}")
    for prop in ("custom_function_name", "event_reference", "bCallInEditor"):
        try:
            lines.append(f"  {prop}={node.get_editor_property(prop)}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(o.get_name())
        lines.append(f"  pin {pn} dir={unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)} links={linked}")

# list all functions on generated class
cls = item.generated_class()
for fn in cls.get_class().get_functions():
    name = fn.get_name()
    if "Attach" in name or "Sight" in name or "Spawn" in name:
        lines.append(f"UFunction: {name}")

OUT.write_text("\n".join(lines))
