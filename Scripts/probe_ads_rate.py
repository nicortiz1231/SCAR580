"""Probe what sets AnimMovementRate at runtime and current defaults."""
import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ads_rate.log")
AC = "/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralAnimation.AC_ProceduralAnimation"
BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
PISTOL_VALUES = "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/DT_PistolAnimationValues.DT_PistolAnimationValues"


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)


def main():
    if LOG.exists():
        LOG.unlink()

    ac = unreal.load_asset(AC)
    cdo = unreal.get_default_object(ac.generated_class())
    log(f"AC CDO AnimMovementRate={cdo.get_editor_property('AnimMovementRate')}")
    log(f"AC CDO AnimMovementStrenght={cdo.get_editor_property('AnimMovementStrenght')}")
    log(f"AC CDO MovementStrenghtRatioPerWeapon={cdo.get_editor_property('MovementStrenghtRatioPerWeapon')}")

    pv = unreal.load_asset(PISTOL_VALUES)
    wv = unreal.get_default_object(pv.get_class()).get_editor_property("WeaponValues")
    log(f"pistol MovementStrenghtRatio={wv.get_editor_property('MovementStrenghtRatio_44_B1E81033BE4E40A1713F0F81C099EA0B')}")

    # sets to AnimMovementRate in AC
    eg = None
    for graph in unreal.BlueprintEditorLibrary.list_graphs(ac):
        if graph.get_name() == "EventGraph":
            eg = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            break
    if eg:
        for node in eg.list_all_nodes():
            if node.get_class().get_name() != "K2Node_VariableSet":
                continue
            try:
                var = node.get_editor_property("variable_reference")
                if str(var.get_member_name()) != "AnimMovementRate":
                    continue
                log(f"AC set AnimMovementRate: {node.get_name()} in EventGraph")
            except Exception:
                pass
        for node in eg.list_all_nodes():
            if "MacroInstance" not in node.get_class().get_name():
                continue
            pin = node.find_input_pin("PlayRate")
            if not pin:
                continue
            links = unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)
            if not links:
                continue
            owner = unreal.BlueprintGraphPinLibrary.get_owning_node(links[0])
            log(f"timeline macro {node.get_name()} PlayRate <- {owner.get_name() if owner else '?'}")

    log("done")


main()
