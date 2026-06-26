import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_scope_state.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
for prop in ("ScopeSightMesh", "OpticSightMesh", "AimDistanceFromCamera", "ChangeSightSpeed"):
    try:
        val = cdo.get_editor_property(prop)
        lines.append(f"{prop}={val.get_path_name() if hasattr(val,'get_path_name') else val}")
    except Exception as exc:
        lines.append(f"{prop} ERR {exc}")

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "OpticSight" not in obj.get_name():
        continue
    if obj.get_class().get_name() != "StaticMeshComponent":
        continue
    lines.append(f"component={obj.get_name()}")
    for prop in ("static_mesh", "visible", "hidden_in_game", "relative_location", "relative_rotation", "relative_scale3d"):
        try:
            val = obj.get_editor_property(prop)
            if hasattr(val, "get_path_name"):
                lines.append(f"  {prop}={val.get_path_name()}")
            else:
                lines.append(f"  {prop}={val!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

editor = unreal.BlueprintGraphEditor.get_graph_editor(
    unreal.BlueprintEditorLibrary.find_event_graph(sniper)
)
lines.append("=== EventGraph ===")
for node in editor.list_all_nodes():
    title = str(node.get_node_title()).replace("\n", " | ")
    lines.append(f"  {node.get_name()} | {title}")
    if "SetStaticMesh" in title:
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if pn in ("execute", "then", "self", "NewMesh"):
                linked = []
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    linked.append(lp.get_owning_node().get_name())
                try:
                    val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                    if val:
                        linked.append(val)
                except Exception:
                    pass
                lines.append(f"    {pn} -> {linked}")

OUT.write_text("\n".join(lines))
