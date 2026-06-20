"""Probe BP_FPCharacter variables and graph nodes related to bodycam PP."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_disable.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())

p("=== BP variables (fish/vignette/bodycam/fov) ===")
for var in unreal.BlueprintEditorLibrary.get_blueprint_variable_details(bp):
    name = str(var.name)
    if any(k in name.lower() for k in ("fish", "vign", "body", "fov", "camera", "lens", "blend")):
        p(f"  {name} type={var.var_type} default={var.default_value}")

p("=== CDO props ===")
for prop in (
    "BODYCAM",
    "FOV_Base",
    "FishEye",
    "Vignette",
    "EnableFishEye",
    "EnableVignette",
    "FishEyeIntensity",
    "VignetteIntensity",
):
    try:
        p(f"  {prop}={cdo.get_editor_property(prop)}")
    except Exception as exc:
        p(f"  {prop}: {exc}")

keywords = ("fish", "vign", "blendable", "post process", "bodycam", "lens", "fov", "viewport")
for graph_name in ("EventGraph", "BeginSetup", "UserConstructionScript"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != graph_name:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        p(f"=== {graph_name} matching nodes ===")
        for node in editor.list_all_nodes():
            try:
                title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
            except Exception:
                title = node.get_class().get_name()
            low = title.lower()
            if any(k in low for k in keywords):
                p(f"  {node.get_name()} :: {title}")

# AC_BodycamCamera component blueprint
ac = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera.AC_BodycamCamera")
p("=== AC_BodycamCamera graphs ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(ac):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    p(f"graph {g.get_name()} nodes={len(editor.list_all_nodes())}")
    for node in editor.list_all_nodes():
        try:
            title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
        except Exception:
            title = node.get_class().get_name()
        low = title.lower()
        if any(k in low for k in keywords) or node.get_class().get_name() in ("K2Node_CallFunction", "K2Node_VariableSet"):
            p(f"  {node.get_name()} :: {title}")

OUT.write_text("\n".join(lines))
