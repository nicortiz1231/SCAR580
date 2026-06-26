"""Trace AnimMovementRate sources and aim timeline macros."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ads_rate2.log")
AC = "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def title(node):
    return str(node.get_node_title()).replace("\n", " | ")


def trace_varget(editor, node_name):
    node = None
    for n in editor.list_all_nodes():
        if n.get_name() == node_name:
            node = n
            break
    if not node:
        return
    try:
        var = node.get_editor_property("variable_reference")
        log(f"{node_name} gets {var.get_member_name()}")
    except Exception:
        log(f"{node_name} title={title(node)}")


def main():
    if LOG.exists():
        LOG.unlink()

    ac = unreal.load_asset(AC)
    for graph in unreal.BlueprintEditorLibrary.list_graphs(ac):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            t = title(node)
            if "ChangeMovement" in t or "MovementStrenght" in t:
                log(f"{graph.get_name()} {node.get_name()} | {t}")
            if node.get_class().get_name() == "K2Node_VariableSet":
                try:
                    var = node.get_editor_property("variable_reference")
                    name = str(var.get_member_name())
                    if "Movement" in name or "Anim" in name:
                        log(f"SET {graph.get_name()} {node.get_name()} {name}")
                except Exception:
                    pass

    eg = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(ac):
        if graph.get_name() == "EventGraph":
            eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    if eg:
        for name in (
            "K2Node_VariableGet_4",
            "K2Node_VariableGet_26",
            "K2Node_VariableGet_137",
            "K2Node_Knot_28",
            "K2Node_MacroInstance_6",
            "K2Node_MacroInstance_1",
            "K2Node_MacroInstance_8",
        ):
            trace_varget(eg, name)
        for node in eg.list_all_nodes():
            if node.get_name() != "K2Node_MacroInstance_8":
                continue
            pin = node.find_input_pin("PlayRate")
            if pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                    owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
                    log(f"MacroInstance_8 PlayRate <- {owner.get_name() if owner else '?'}")
            play = node.find_input_pin("Play")
            if play:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(play):
                    owner = unreal.BlueprintGraphPinLibrary.get_owning_node(lp)
                    log(f"MacroInstance_8 Play <- {owner.get_name() if owner else '?'} | {title(owner) if owner else ''}")

    log("done")


main()
