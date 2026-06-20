import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fps_gamemode.log")
lines = []


def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


def dump_gm(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        p(f"MISSING {path}")
        return
    bp = unreal.load_asset(path)
    cdo = unreal.get_default_object(bp.generated_class())
    p(f"=== {path} ===")
    for prop in (
        "default_pawn_class",
        "player_controller_class",
        "hud_class",
        "player_state_class",
        "game_state_class",
        "spectator_class",
    ):
        try:
            val = cdo.get_editor_property(prop)
            p(f"  {prop}={val.get_name() if val else None}")
        except Exception as exc:
            p(f"  {prop} ERR {exc}")


for asset in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True):
    name = asset.split("/")[-1]
    if name.startswith("GM_") and not name.endswith("_C"):
        dump_gm(asset)

# Map_AR level blueprint nodes
MAP = "/Game/SCAR580/Maps/Map_AR"
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
cls = unreal.load_class(None, "/Game/SCAR580/Maps/Map_AR.Map_AR_C")
result = unreal.BlueprintEditorLibrary.get_blueprint_for_class(cls)
bp = result[0] if isinstance(result, tuple) else result
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
nodes = graph.get_nodes() if hasattr(graph, "get_nodes") else graph.get_editor_property("nodes")
p(f"Map_AR level BP nodes={len(nodes)}")
for node in nodes:
    p(f"  {node.get_node_title(unreal.NodeTitleType.FULL_TITLE)}")

OUT.write_text("\n".join(lines))
