import unreal

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    if "Recoil" in title or node.get_name() == "K2Node_CallFunction_153":
        unreal.log(f"NODE {node.get_name()} | {title}")
        for pin_name in ("execute", "then", "ReturnValue"):
            pin = node.find_input_pin(pin_name) or node.find_output_pin(pin_name)
            if not pin:
                continue
            links = unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
            unreal.log(f"  {pin_name} links={len(links)} dir={pin.get_pin_direction()}")
            for lp in links:
                n = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
                unreal.log(f"    -> {n.get_name() if n else '?'}:{lp.get_pin_name()}")

# Find all exec entry events
for node in editor.list_all_nodes():
    cls = node.get_class().get_name()
    if cls in ("K2Node_Event", "K2Node_CustomEvent", "K2Node_EnhancedInputAction"):
        title = str(node.get_node_title()).replace("\n", " | ")
        then = node.find_then_pin()
        links = unreal.BlueprintGraphPinLibrary.list_connected_pins(then) if then else []
        if links:
            unreal.log(f"EVENT {node.get_name()} | {title} -> {len(links)} exec outs")
