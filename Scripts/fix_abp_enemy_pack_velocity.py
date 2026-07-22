"""Fix ABP_Enemy_Pack Set Velocity Accessed None spam.

Root cause: EventGraph casts TryGetPawnOwner to BP_Enemy, but pack pawns use
BP_Enemy_ZombiePack (sibling of BP_Enemy, not a child). Cast fails -> BP Enemy
is None every tick.

Fix (pack ABP only — kit ABP_Enemy untouched):
  1) Retarget DynamicCast target from BP_Enemy -> Character
  2) Retype variable 'BP Enemy' to Character
  3) Soft-reparent BP_Enemy_ZombiePack under BP_Enemy so kit cast would also work
"""

from __future__ import annotations

import unreal

ABP_PATH = "/Game/SCAR580/Zombies/ABP_Enemy_Pack.ABP_Enemy_Pack"
PACK_BP_PATH = "/Game/SCAR580/Zombies/BP_Enemy_ZombiePack.BP_Enemy_ZombiePack"
KIT_BP_PATH = "/Game/FirstPersonHorrorKit/Blueprints/Enemy/BP_Enemy.BP_Enemy"


def _log(msg: str) -> None:
    unreal.log(f"[fix_abp_pack] {msg}")


def _save(asset) -> None:
    unreal.EditorAssetLibrary.save_asset(asset.get_path_name(), only_if_is_dirty=False)


def _graphs(bp) -> list:
    graphs = []
    for prop in ("ubergraph_pages", "function_graphs", "event_graphs"):
        try:
            pages = bp.get_editor_property(prop)
        except Exception:
            pages = None
        if pages:
            graphs.extend(list(pages))
    # AnimBP may expose differently
    for attr in ("ubergraph_pages", "function_graphs"):
        if hasattr(bp, attr):
            try:
                val = getattr(bp, attr)
                if val:
                    for g in val:
                        if g not in graphs:
                            graphs.append(g)
            except Exception:
                pass
    return graphs


def fix_abp_cast_and_variable() -> bool:
    bp = unreal.load_asset(ABP_PATH)
    if not bp:
        _log(f"FAIL: missing {ABP_PATH}")
        return False

    character_cls = unreal.Character.static_class()
    cast_fixed = 0
    var_fixed = False

    # --- Retarget cast nodes ---
    for graph in _graphs(bp):
        gname = graph.get_name() if graph else "?"
        nodes = []
        try:
            nodes = list(graph.nodes)
        except Exception:
            try:
                nodes = list(graph.get_editor_property("nodes"))
            except Exception:
                nodes = []
        for node in nodes:
            try:
                title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
            except Exception:
                title = node.get_name()
            cls_name = node.get_class().get_name()
            if "DynamicCast" not in cls_name and "Cast To BP_Enemy" not in title and "Cast To BP Enemy" not in title:
                # Still try if title mentions BP_Enemy cast
                if "Cast To" not in title or "BP_Enemy" not in title.replace(" ", "_"):
                    if "Cast To BP" not in title:
                        continue

            if "BP_Enemy" not in title and "BP Enemy" not in title and "DynamicCast" not in cls_name:
                continue
            if "DynamicCast" not in cls_name and "Cast To" not in title:
                continue

            # Prefer BP_Enemy cast specifically
            if "DynamicCast" in cls_name or "BP_Enemy" in title or "BP Enemy" in title:
                for prop in ("target_type", "TargetType"):
                    try:
                        node.set_editor_property(prop, character_cls)
                        cast_fixed += 1
                        _log(f"Retargeted cast in {gname}/{node.get_name()} ({title}) -> Character")
                        break
                    except Exception as e:
                        _log(f"set {prop} failed on {node.get_name()}: {e}")

    # Broader pass: any K2Node_DynamicCast in EventGraph
    for graph in _graphs(bp):
        gname = graph.get_name() if graph else "?"
        if gname not in ("EventGraph", "Event Graph"):
            # Still scan all ubergraphs
            pass
        try:
            nodes = list(graph.nodes)
        except Exception:
            continue
        for node in nodes:
            if "DynamicCast" not in node.get_class().get_name():
                continue
            try:
                cur = node.get_editor_property("target_type")
            except Exception:
                cur = None
            cur_name = ""
            try:
                cur_name = cur.get_name() if cur else ""
            except Exception:
                cur_name = str(cur)
            if cur_name and "Character" == cur_name:
                continue
            # If still pointing at BP_Enemy (or anything kit-specific), retarget
            if "Enemy" in cur_name or not cur_name or "BP_Enemy" in cur_name:
                try:
                    node.set_editor_property("target_type", character_cls)
                    cast_fixed += 1
                    _log(f"Retargeted {gname}/{node.get_name()} target_type {cur_name!r} -> Character")
                except Exception as e:
                    _log(f"DynamicCast retarget failed: {e}")

    # --- Retype variable BP Enemy ---
    try:
        # SoftObjectPath / pin type via BlueprintEditorLibrary if available
        new_type = unreal.EdGraphPinType()
        new_type.pin_category = "object"
        new_type.pin_sub_category_object = character_cls
        # Find variable
        for var in bp.new_variables if hasattr(bp, "new_variables") else bp.get_editor_property("new_variables"):
            vname = var.var_name
            if str(vname) in ("BP Enemy", "BP_Enemy", "bp_enemy"):
                try:
                    var.var_type = new_type
                    var_fixed = True
                    _log(f"Retyped variable {vname} -> Character object")
                except Exception as e:
                    _log(f"Direct var_type assign failed: {e}")
                    try:
                        var.set_editor_property("var_type", new_type)
                        var_fixed = True
                        _log(f"Retyped variable {vname} via set_editor_property")
                    except Exception as e2:
                        _log(f"var set_editor_property failed: {e2}")
    except Exception as e:
        _log(f"Variable retype pass failed: {e}")

    # Alternative: BlueprintEditorLibrary.change_variable_type if present
    if not var_fixed and hasattr(unreal.BlueprintEditorLibrary, "change_variable_type"):
        try:
            unreal.BlueprintEditorLibrary.change_variable_type(
                bp, "BP Enemy", unreal.PropertyType.OBJECT, character_cls
            )
            var_fixed = True
            _log("change_variable_type(BP Enemy -> Character) OK")
        except Exception as e:
            _log(f"change_variable_type failed: {e}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    _save(bp)
    _log(f"ABP compile/save done cast_fixed={cast_fixed} var_fixed={var_fixed}")
    return cast_fixed > 0 or var_fixed


def reparent_pack_bp() -> bool:
    """Make pack BP a child of kit BP_Enemy so existing casts succeed."""
    pack = unreal.load_asset(PACK_BP_PATH)
    kit = unreal.load_asset(KIT_BP_PATH)
    if not pack or not kit:
        _log(f"reparent skip: pack={bool(pack)} kit={bool(kit)}")
        return False

    kit_cls = kit.generated_class()
    try:
        parent = pack.parent_class
        parent_name = parent.get_name() if parent else "?"
    except Exception:
        parent_name = "?"
    _log(f"BP_Enemy_ZombiePack parent before: {parent_name}")

    if parent_name and "BP_Enemy_C" in parent_name and "ZombiePack" not in parent_name:
        _log("Already parented under BP_Enemy")
        return True

    try:
        unreal.BlueprintEditorLibrary.reparent_blueprint(pack, kit_cls)
        unreal.BlueprintEditorLibrary.compile_blueprint(pack)
        _save(pack)
        _log(f"Reparented BP_Enemy_ZombiePack under {kit_cls.get_name()}")
        return True
    except Exception as e:
        _log(f"reparent_blueprint failed: {e}")
        return False


def verify() -> None:
    abp = unreal.load_asset(ABP_PATH)
    pack = unreal.load_asset(PACK_BP_PATH)
    if abp:
        for graph in _graphs(abp):
            try:
                nodes = list(graph.nodes)
            except Exception:
                continue
            for node in nodes:
                if "DynamicCast" not in node.get_class().get_name():
                    continue
                try:
                    t = node.get_editor_property("target_type")
                    _log(f"VERIFY cast {graph.get_name()}/{node.get_name()} -> {t.get_name() if t else None}")
                except Exception as e:
                    _log(f"VERIFY cast read fail: {e}")
        for var in abp.get_editor_property("new_variables"):
            if str(var.var_name) in ("BP Enemy", "BP_Enemy"):
                vt = var.var_type
                sub = None
                try:
                    sub = vt.pin_sub_category_object
                except Exception:
                    pass
                _log(f"VERIFY var {var.var_name} category={vt.pin_category} sub={sub.get_name() if sub else None}")
    if pack:
        try:
            _log(f"VERIFY pack parent={pack.parent_class.get_name()}")
        except Exception as e:
            _log(f"VERIFY pack parent fail: {e}")


def main() -> None:
    ok_abp = fix_abp_cast_and_variable()
    ok_parent = reparent_pack_bp()
    verify()
    _log(f"DONE abp={ok_abp} reparent={ok_parent}")


if __name__ == "__main__":
    main()
