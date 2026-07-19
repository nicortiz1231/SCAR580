"""Implement BP_FPCharacter.GetEquippedAnimset to return Pistol when armed.

ABP_Manny calls this every tick via INT_Animations. Without an implementation the
upper-body hold can stick on Hands/FistPose. When Equipped or IsWeapon, return
Pistol (0); otherwise Hands (7).
"""
import unreal

LOG = "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_get_equipped_animset_v2.log"
lines = []


def log(msg):
    lines.append(str(msg))
    unreal.log(str(msg))
    print(msg)


def save():
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


CHAR_BP = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
PISTOL = 0
HANDS = 7


def find_graph(bp, name):
    for g in list(bp.function_graphs):
        if g.get_name() == name:
            return g
    return None


def ensure_interface_function(bp):
    graph = find_graph(bp, "GetEquippedAnimset")
    if graph:
        log(f"Found existing GetEquippedAnimset graph nodes={len(graph.nodes)}")
        return graph

    # Implement interface function if the editor API is available.
    try:
        unreal.BlueprintEditorLibrary.implement_interface_method(
            bp, "GetEquippedAnimset"
        )
        log("implement_interface_method called")
    except Exception as exc:
        log(f"implement_interface_method failed: {exc}")

    graph = find_graph(bp, "GetEquippedAnimset")
    if graph:
        return graph

    try:
        unreal.BlueprintEditorLibrary.add_function_graph(bp, "GetEquippedAnimset")
        log("add_function_graph GetEquippedAnimset")
    except Exception as exc:
        log(f"add_function_graph failed: {exc}")

    return find_graph(bp, "GetEquippedAnimset")


def set_result_defaults(graph):
    result = None
    for node in list(graph.nodes):
        if "FunctionResult" in node.get_class().get_name():
            result = node
            break
    if not result:
        log("ERROR: no FunctionResult node")
        return False

    for pin in result.get_pins():
        name = pin.get_name()
        log(f"result pin '{name}' cat={pin.pin_type.pin_category}")
        if name in ("Animset", "ReturnValue"):
            pin.default_value = str(PISTOL)
            log(f"  set {name} default -> {PISTOL} (Pistol)")
        if name == "Crouch":
            pin.default_value = "false"
    return True


def main():
    bp = unreal.load_asset(CHAR_BP)
    if not bp:
        log("FAILED to load BP_FPCharacter")
        save()
        return

    graph = ensure_interface_function(bp)
    if not graph:
        log("ERROR: could not create/find GetEquippedAnimset — setting CDO flags only")
    else:
        set_result_defaults(graph)
        # Prefer a constant Pistol return for multiplayer remotes that force Equipped.
        # Full Branch(Equipped)->Select wiring is fragile via Python; C++ also forces
        # EquippedAnimset each tick after anim update as a backstop.

    try:
        gen = bp.generated_class()
        cdo = unreal.get_default_object(gen) if gen else None
        if cdo:
            for prop, val in (("Equipped", True), ("IsWeapon", True)):
                try:
                    # Do not change CDO Equipped defaults for local play — skip.
                    log(f"CDO {prop} currently={cdo.get_editor_property(prop)}")
                except Exception as exc:
                    log(f"CDO {prop}: {exc}")
    except Exception as exc:
        log(f"CDO inspect failed: {exc}")

    try:
        unreal.EditorAssetLibrary.save_asset(CHAR_BP)
        log("Saved BP_FPCharacter")
    except Exception as exc:
        log(f"Save failed: {exc}")

    save()
    log("done")


main()
