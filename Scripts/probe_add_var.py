import unreal

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

for var in ("MobileTouchPrevX", "MobileTouchPrevY", "MobileTouchHasPrev", "IsAim"):
    node = editor.add_get_member_variable_node(var)
    unreal.log(f"GET {var} class={node.get_class().get_name()}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        name = unreal.BlueprintGraphPinLibrary.get_pin_name(pin)
        direction = unreal.BlueprintGraphPinLibrary.get_pin_direction(pin)
        unreal.log(f"  pin {name} dir={direction}")
