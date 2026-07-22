"""Restore FirstPersonHorrorKit zombie wiring for SCAR pawns.

- Perception: accept any Character (not only BP_FirstPersonCharacter)
- CanAttack? default true (kit attack gate)
- Bone: leave empty (kit default — Physical_Animation no-ops safely)
- BTTask_Chase_Player: OnFail -> FinishExecute(false) so MoveTo can retry
"""

import unreal

ENEMY = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy.BP_Enemy"
CHASE = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/Ai_Behavior/Tasks/BTTask_Chase_Player.BTTask_Chase_Player"


def _save(asset):
    unreal.EditorAssetLibrary.save_asset(asset.get_path_name(), only_if_is_dirty=False)


def fix_enemy():
    bp = unreal.load_asset(ENEMY)
    if not bp:
        unreal.log_error(f"Missing {ENEMY}")
        return

    cdo = unreal.get_default_object(bp.generated_class())
    # CanAttack? is a bool on the CDO
    if hasattr(cdo, "can_attack_"):
        cdo.set_editor_property("can_attack_", True)
    elif hasattr(cdo, "CanAttack?"):
        pass

    # Prefer Pythonized name variants used by UE reflection
    for prop in ("can_attack_", "can_attack", "CanAttack?"):
        try:
            cdo.set_editor_property(prop, True)
            unreal.log(f"Set {prop}=True")
            break
        except Exception:
            continue

    # Keep Bone empty (kit default)
    for prop in ("bone", "Bone"):
        try:
            cdo.set_editor_property(prop, "None")
            unreal.log(f"Reset {prop} to None")
            break
        except Exception:
            continue

    graph = None
    for g in bp.get_editor_property("ubergraph_pages"):
        if g.get_name() == "EventGraph":
            graph = g
            break
    if not graph:
        unreal.log_error("No EventGraph on BP_Enemy")
        return

    # Soften Cast To BP_FirstPersonCharacter -> Cast To Character
    cast_nodes = []
    for node in graph.nodes:
        title = ""
        try:
            title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
        except Exception:
            title = str(node)
        if "Cast To BP_FirstPersonCharacter" in title or "Cast To BP First Person Character" in title:
            cast_nodes.append(node)

    character_class = unreal.Character.static_class()
    for node in cast_nodes:
        try:
            # K2Node_DynamicCast has set_target_type in some versions; else replace pin
            if hasattr(node, "set_editor_property"):
                try:
                    node.set_editor_property("target_type", character_class)
                    unreal.log("Retargeted perception cast to Character")
                    continue
                except Exception:
                    pass
            # Fallback: use blueprint editor library helpers if available
            unreal.log_warning(f"Could not retarget cast node {node.get_name()} via property")
        except Exception as e:
            unreal.log_warning(f"Cast retarget failed: {e}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    _save(bp)
    unreal.log("BP_Enemy updated")


def fix_chase_task():
    bp = unreal.load_asset(CHASE)
    if not bp:
        unreal.log_error(f"Missing {CHASE}")
        return

    graph = None
    for g in bp.ubergraph_pages if hasattr(bp, "ubergraph_pages") else bp.get_editor_property("ubergraph_pages"):
        if g.get_name() == "EventGraph":
            graph = g
            break
    if not graph:
        unreal.log_error("No EventGraph on chase task")
        return

    move_to = None
    finish = None
    for node in graph.nodes:
        try:
            title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
        except Exception:
            title = ""
        if "AI MoveTo" in title:
            move_to = node
        if "Finish Execute" in title:
            finish = node

    if not move_to or not finish:
        unreal.log_error(f"Missing nodes move={move_to} finish={finish}")
        return

    # Wire OnFail -> Finish Execute (bSuccess left false by default)
    try:
        on_fail = None
        for pin in move_to.get_pins():
            if pin.get_name() == "OnFail":
                on_fail = pin
                break
        exec_in = None
        for pin in finish.get_pins():
            if pin.get_name() == "execute":
                exec_in = pin
                break
        if on_fail and exec_in:
            # Only connect if OnFail has no links
            if len(on_fail.linked_to) == 0:
                on_fail.make_link_to(exec_in)
                unreal.log("Wired AI MoveTo OnFail -> Finish Execute")
            else:
                unreal.log("OnFail already wired")
        else:
            unreal.log_error("Could not find OnFail/execute pins")
    except Exception as e:
        unreal.log_error(f"Chase OnFail wire failed: {e}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    _save(bp)
    unreal.log("BTTask_Chase_Player updated")


def main():
    fix_enemy()
    fix_chase_task()
    unreal.log("HorrorKit zombie kit restore done")


main()
