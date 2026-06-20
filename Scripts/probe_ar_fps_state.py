"""Probe Map_AR + BP_FPCharacter camera/weapon setup state."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ar_fps_state.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


def dump_gm(path):
    bp = unreal.load_asset(path)
    if not bp:
        p(f"MISSING {path}")
        return
    cdo = unreal.get_default_object(bp.generated_class())
    p(f"=== {path} ===")
    for prop in ("default_pawn_class", "player_controller_class", "hud_class"):
        val = cdo.get_editor_property(prop)
        p(f"  {prop}={val.get_name() if val else None}")


def dump_component_template(bp, comp_name):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not obj or comp_name not in obj.get_name():
            continue
        cls = obj.get_class().get_name()
        p(f"  {comp_name} ({cls})")
        for prop in (
            "target_arm_length",
            "TargetArmLength",
            "socket_offset",
            "SocketOffset",
            "relative_location",
            "RelativeLocation",
            "field_of_view",
            "FieldOfView",
            "use_pawn_control_rotation",
            "bUsePawnControlRotation",
            "post_process_blend_weight",
        ):
            try:
                p(f"    {prop}={obj.get_editor_property(prop)}")
            except Exception:
                pass


def dump_graph_titles(bp, graph_name):
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        if g.get_name() != graph_name:
            continue
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        p(f"=== graph {graph_name} nodes={len(editor.list_all_nodes())} ===")
        for node in editor.list_all_nodes():
            try:
                title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
            except Exception:
                title = node.get_class().get_name()
            p(f"  {node.get_name()} :: {title}")


# Game modes
dump_gm("/Game/SCAR580/Blueprints/GameModes/GM_SCAR_AR.GM_SCAR_AR")
dump_gm("/Game/BodycamFPSKIT/Blueprints/GameModes/GM_FP.GM_FP")

# AR session
config = unreal.load_asset("/Game/HandheldAR/D_ARSessionConfig")
if config:
    p("=== D_ARSessionConfig ===")
    for prop in ("bEnableAutomaticCameraOverlay", "bEnableAutomaticCameraTracking"):
        try:
            p(f"  {prop}={config.get_editor_property(prop)}")
        except Exception as exc:
            p(f"  {prop} ERR {exc}")

# Character components
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
p("=== BP_FPCharacter components ===")
dump_component_template(bp, "SpringArm")
dump_component_template(bp, "FirstPersonCamera")

cdo = unreal.get_default_object(bp.generated_class())
p(f"BODYCAM={cdo.get_editor_property('BODYCAM')}")

# Event graph + any custom graphs
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    name = g.get_name()
    if name in ("EventGraph", "BeginSetup", "ConstructionScript"):
        dump_graph_titles(bp, name)

# Map_AR world settings + actors
MAP = "/Game/SCAR580/Maps/Map_AR"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ws = world.get_world_settings()
p(f"Map_AR default_game_mode={ws.get_editor_property('default_game_mode').get_name()}")

for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor.static_class()):
    cls = actor.get_class().get_name()
    label = actor.get_actor_label()
    if any(k in cls for k in ("Character", "Pawn", "Player", "AR", "PostProcess", "Light")) or "Map_AR" in cls:
        p(f"actor {label} ({cls}) hidden={actor.is_hidden_ed()}")

# Search for AR character assets
p("=== AR/Character assets under /Game ===")
for asset in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True):
    base = asset.split("/")[-1]
    if any(k in base for k in ("AR_Character", "FirstPersonCharacter", "BP_AR", "BP_FP")):
        p(f"  {asset}")

OUT.write_text("\n".join(lines))
