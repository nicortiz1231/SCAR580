import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_beginplay.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    gname = graph.get_name()
    if gname not in ("EventGraph", "BeginSetup", "ConstructionScript"):
        continue
    p(f"graph={gname}")
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
        p(f"  {node.get_class().get_name()}: {title}")

# Spring arm / camera defaults from SCS
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj:
        continue
    name = obj.get_name()
    if any(k in name for k in ("Camera", "SpringArm", "Mesh")):
        p(f"component {name} class={obj.get_class().get_name()}")
        for prop in ("relative_location", "RelativeLocation", "target_arm_length", "TargetArmLength", "field_of_view", "FieldOfView"):
            try:
                p(f"  {prop}={obj.get_editor_property(prop)}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
