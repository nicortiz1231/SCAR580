"""Find BulletCasingSys usage on BP_FPCharacter."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bullet_casing.log")
BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"


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
            if node.get_class().get_name() == "K2Node_SpawnActorFromClass":
                log(f"{graph.get_name()} {node.get_name()} | {t}")
            if node.get_class().get_name() == "K2Node_VariableGet":
                try:
                    var = node.get_editor_property("variable_reference")
                    if "Bullet" in str(var.get_member_name()) or "Casing" in str(var.get_member_name()):
                        log(f"{graph.get_name()} {node.get_name()} | Get {var.get_member_name()}")
                except Exception:
                    pass

    log("done")


main()
