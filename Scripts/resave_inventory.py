"""Force-save clean WBP_Inventory EventGraph (Construct -> Setup only)."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/resave_inventory.log")
INV = "/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Switcher/WBP_Inventory"


def log(m):
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + m + "\n", encoding="utf-8")
    unreal.log(m)


bp = unreal.load_asset(INV)
eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
nodes = list(editor.list_all_nodes()) if hasattr(editor, "list_all_nodes") else list(eg.nodes)
for n in nodes:
    try:
        t = str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE))
    except Exception:
        t = n.get_class().get_name()
    log(f"NODE {n.get_name()} {t}")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
log(f"saved={unreal.EditorAssetLibrary.save_asset(INV, only_if_is_dirty=False)}")
