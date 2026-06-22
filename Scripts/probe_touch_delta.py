import unreal

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)

float_type = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, "MouseSens")

names = [n for n in unreal.BlueprintEditorLibrary.list_member_variable_names(bp) if "Prev" in n or "Touch" in n]
for n in names:
    t = unreal.BlueprintEditorLibrary.get_member_variable_type(bp, n)
    unreal.log(f"VAR {n} -> {t}")

unreal.BlueprintEditorLibrary.change_member_variable_type(bp, "MobileTouchPrevY", float_type)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)

sub = editor.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble")
get_y1 = editor.add_get_member_variable_node("MobileTouchPrevY")
get_y2 = editor.add_get_member_variable_node("MobileTouchPrevY")
for idx, get_y in enumerate((get_y1, get_y2), 1):
    out = get_y.find_output_pin("MobileTouchPrevY")
    ok = out.try_create_connection(sub.find_input_pin("A"))
    unreal.log(f"get_y{idx} connect: {ok}")
    if ok:
        unreal.BlueprintGraphPinLibrary.break_pin_links(sub.find_input_pin("A"))

# Try rename approach: create new var name
new_name = "MobileTouchLastY"
if new_name not in names:
    editor.add_member_variable(new_name, float_type)
get_new = editor.add_get_member_variable_node(new_name)
ok = get_new.find_output_pin(new_name).try_create_connection(sub.find_input_pin("A"))
unreal.log(f"{new_name} connect: {ok}")
