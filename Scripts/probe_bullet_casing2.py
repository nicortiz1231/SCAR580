"""Find BulletCasingSys nodes across item base graphs."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bullet_casing2.log")
BP = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def main():
    if LOG.exists():
        LOG.unlink()

    bp = unreal.load_asset(BP)
    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            t = title(node)
            if "Bullet" in t or "Casing" in t or "Shell" in t:
                log(f"{graph.get_name()} {node.get_name()} | {t}")
            cls = node.get_class().get_name()
            if cls in ("K2Node_VariableGet", "K2Node_VariableSet"):
                try:
                    var = str(node.get_editor_property("variable_reference").get_member_name())
                    if "Bullet" in var or "Casing" in var or "Shell" in var:
                        log(f"{graph.get_name()} {node.get_name()} | {cls} {var}")
                except Exception:
                    pass

    log("done")


main()
