"""Read MacroInstance_8 PlayRate default and what VariableSet_60 does."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ads_rate5.log")
AC = "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def main():
    if LOG.exists():
        LOG.unlink()

    ac = unreal.load_asset(AC)
    eg = unreal.BlueprintGraphEditor.get_graph_editor(
        next(g for g in unreal.BlueprintEditorLibrary.list_graphs(ac) if g.get_name() == "EventGraph")
    )
    mi8 = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_MacroInstance_8")
    pr = mi8.find_input_pin("PlayRate")
    for fn in ("get_default_value", "get_default_as_string"):
        try:
            log(f"PlayRate {fn}={getattr(pr, fn)()}")
        except Exception as e:
            log(f"PlayRate {fn} err={e}")
    try:
        log(f"PlayRate pin_value={unreal.BlueprintGraphPinLibrary.get_pin_value(pr)}")
    except Exception as e:
        log(f"pin_value err={e}")

    for name in ("K2Node_VariableSet_60", "K2Node_VariableSet_37", "K2Node_IfThenElse_2"):
        node = next((n for n in eg.list_all_nodes() if n.get_name() == name), None)
        if not node:
            continue
        log(f"{name} | {str(node.get_node_title()).replace(chr(10),'|')}")
        try:
            var = node.get_editor_property("variable_reference")
            log(f"  var={var.get_member_name()}")
        except Exception:
            pass

    vg4 = next(n for n in eg.list_all_nodes() if n.get_name() == "K2Node_VariableGet_4")
    out = vg4.find_output_pin("AnimMovementRate") or vg4.find_output_pin("ReturnValue")
    log(f"VariableGet_4 out links={len(unreal.BlueprintGraphPinLibrary.list_connected_pins(out))}")
    log("done")


main()
