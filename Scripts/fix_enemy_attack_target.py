"""Make BP_Enemy attack compare hits against GetPlayerCharacter (SCAR-compatible)."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_enemy_attack_target.log")
ENEMY_BP = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy"
GET_PLAYER_FN = "/Script/Engine.GameplayStatics:GetPlayerCharacter"


def log(msg: str) -> None:
    prev = OUT.read_text() if OUT.exists() else ""
    OUT.write_text(prev + str(msg) + "\n")
    unreal.log(f"[fix_enemy_attack] {msg}")
    print(msg)


def connect(src, dst) -> bool:
    return bool(src and dst and src.try_create_connection(dst))


def break_all(pin) -> None:
    if pin:
        pin.break_pin_links()


def pin_named(node, name, direction=None):
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        if str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) != name:
            continue
        if direction is None or unreal.BlueprintGraphPinLibrary.get_pin_direction(pin) == direction:
            return pin
    return None


def main():
    if OUT.exists():
        OUT.unlink()

    bp = unreal.load_asset(f"{ENEMY_BP}.BP_Enemy")
    eg = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )

    equal_node = None
    for node in eg.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " ")
        if "Equal (Object)" in title or title.strip() == "Equal (Object)":
            equal_node = node
            log(f"Found equal node {node.get_name()}")
            break

    if not equal_node:
        # fallback: search by class
        for node in eg.list_all_nodes():
            if "PromotableOperator" in node.get_class().get_name():
                a = pin_named(node, "A")
                b = pin_named(node, "B")
                if a and b:
                    equal_node = node
                    log(f"Fallback equal candidate {node.get_name()} title={node.get_node_title()}")
                    break

    if not equal_node:
        raise RuntimeError("Could not find Equal(Object) used for attack hit check")

    pin_a = pin_named(equal_node, "A", unreal.EdGraphPinDirection.EGPD_INPUT)
    if not pin_a:
        raise RuntimeError("Equal node missing pin A")

    # Break old perception cast feed into A
    break_all(pin_a)

    get_player = None
    for node in eg.list_all_nodes():
        if "Get Player Character" in str(node.get_node_title()):
            get_player = node
            break
    if not get_player:
        get_player = eg.add_call_function_node(GET_PLAYER_FN)
        log(f"Added GetPlayerCharacter {get_player.get_name() if get_player else None}")
    if not get_player:
        raise RuntimeError("Failed to create GetPlayerCharacter")

    out = pin_named(get_player, "ReturnValue", unreal.EdGraphPinDirection.EGPD_OUTPUT)
    ok = connect(out, pin_a)
    log(f"Wired GetPlayerCharacter -> Equal.A = {ok}")

    # Keep CanAttack default true via CDO
    cdo = unreal.get_default_object(bp.generated_class())
    for prop in ("CanAttack?", "can_attack?"):
        try:
            cdo.set_editor_property(prop, True)
            log(f"CDO {prop}=True")
        except Exception:
            pass

    bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(ENEMY_BP, only_if_is_dirty=False)
    log("Saved BP_Enemy attack target fix")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"FATAL: {exc}")
        raise
