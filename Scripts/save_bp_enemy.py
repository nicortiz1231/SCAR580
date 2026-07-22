"""Save BP_Enemy after removing BeginPlay Physical_Animation call."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/save_bp_enemy.log")
BP = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy"


def log(m):
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + m + "\n", encoding="utf-8")
    unreal.log(m)


bp = unreal.load_asset(BP)
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
for n in list(editor.list_all_nodes()):
    try:
        t = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE))
    except Exception:
        t = n.get_class().get_name()
    log(f"{n.get_name()} :: {t}")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
log(f"saved={unreal.EditorAssetLibrary.save_asset(BP, only_if_is_dirty=False)}")
