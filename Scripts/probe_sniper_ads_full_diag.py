"""Full sniper ADS diagnostic dump."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_ads_full_diag.log")
lines = []

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))

sniper = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
)
cdo = unreal.get_default_object(sniper.generated_class())
lines.append("=== Sniper ===")
for p in ("AimDistanceFromCamera", "ScopeMat_SightDistance", "ScopeMat_GradientParam", "ScopeRenderRadius"):
    lines.append(f"  {p}={cdo.get_editor_property(p)}")

lines.append("\n=== Select_5 FOV values ===")
for node in eg.list_all_nodes():
    if node.get_name() != "K2Node_Select_5":
        continue
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if val and pn.startswith("NewEnumerator"):
            lines.append(f"  {pn}={val}")

lines.append("\n=== AIMOn chain from K2Node_CallFunction_56 ===")
aim_on = None
for node in eg.list_all_nodes():
    if node.get_name() == "K2Node_CallFunction_56":
        aim_on = node
        break
if aim_on:
    pin = aim_on.find_output_pin("then")
    depth = 0
    seen = set()
    stack = list(unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)) if pin else []
    while stack:
        lp = stack.pop(0)
        n = lp.get_owning_node()
        if n.get_name() in seen:
            continue
        seen.add(n.get_name())
        title = str(n.get_node_title()).replace("\n", " | ")[:80]
        lines.append(f"  {n.get_name()} | {title}")
        then = n.find_output_pin("then")
        if then:
            for x in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
                if x.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT:
                    stack.append(x)

lines.append("\n=== All ExecuteConsoleCommand ===")
for node in eg.list_all_nodes():
    if "ExecuteConsoleCommand" not in str(node.get_node_title()):
        continue
    cmd = node.find_input_pin("Command")
    lines.append(f"  {node.get_name()}: {unreal.BlueprintGraphPinLibrary.get_pin_value(cmd) if cmd else '?'}")

lines.append("\n=== SetVisibility nodes near Aim ===")
for node in eg.list_all_nodes():
    if "SetVisibility" not in str(node.get_node_title()):
        continue
    vis = node.find_input_pin("bNewVisibility")
    val = unreal.BlueprintGraphPinLibrary.get_pin_value(vis) if vis else "?"
    lines.append(f"  {node.get_name()} visible={val}")

# Camera template
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(char):
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    )
    if obj and "FirstPersonCamera" in obj.get_name():
        lines.append("\n=== FirstPersonCamera template ===")
        for p in ("field_of_view", "first_person_field_of_view", "enable_first_person_field_of_view"):
            try:
                lines.append(f"  {p}={obj.get_editor_property(p)!r}")
            except Exception:
                pass

# BP_Scope
scope = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Attachments/Scope/Blueprints/BP_Scope.BP_Scope")
for g in unreal.BlueprintEditorLibrary.list_graphs(scope):
    if g.get_name() != "UserConstructionScript":
        continue
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"\n=== BP_Scope UCS ({len(ed.list_all_nodes())} nodes) ===")
    for n in ed.list_all_nodes()[:15]:
        lines.append(f"  {n.get_name()} | {str(n.get_node_title()).replace(chr(10),' ')[:60]}")

OUT.write_text("\n".join(lines))
