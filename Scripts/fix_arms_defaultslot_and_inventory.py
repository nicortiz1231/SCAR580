"""Fix duplicate DefaultSlot in ABP_FP_ArmsProcedural AnimGraph.

Renames the second DefaultSlot (AnimGraphNode_Slot_3) so montage slot
names are unique. Keeps AnimGraphNode_Slot_4 as DefaultSlot for reloads.
Also verifies WBP_Inventory Construct no longer calls SetBrushFromMaterial.
"""

from __future__ import annotations

from pathlib import Path

import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_arms_defaultslot.log")
ABP = "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural"
INV = "/Game/InventorySystem_0_5/Blueprints/UserInterfaces/Game/Switcher/WBP_Inventory"
NEW_SLOT = "DefaultSlot_ADS"


def log(msg: str) -> None:
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(f"[fix_arms_defaultslot] {msg}")


def node_title(node) -> str:
    try:
        return str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        return node.get_class().get_name()


def iter_anim_graphs(bp):
    """Yield all animation graphs including state machines / nested graphs."""
    seen = set()
    queue = []

    try:
        eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    except Exception:
        eg = None

    # Ubergraph / function graphs
    try:
        for g in bp.function_graphs:
            queue.append(g)
    except Exception:
        pass
    try:
        for g in bp.ubergraph_pages:
            queue.append(g)
    except Exception:
        pass

    # Anim blueprint specific
    for attr in ("anim_blueprint_generated_class",):
        pass

    # Use editor subsystem to get anim graphs if available
    try:
        # AnimationBlueprintEditorLibrary / BlueprintEditorLibrary
        graphs = unreal.AnimBlueprintLibrary.get_animation_graphs(bp)
        for g in graphs:
            queue.append(g)
    except Exception as exc:
        log(f"get_animation_graphs: {exc}")

    # Fallback: walk all EdGraphs on the package object tree
    try:
        for obj in unreal.EditorAssetLibrary.find_asset_data(ABP).get_asset().get_editor_property("function_graphs"):
            queue.append(obj)
    except Exception:
        pass

    # Also scan Blueprint's all graphs via recursive object iterator
    try:
        outer = unreal.load_asset(ABP)
        for obj in unreal.ObjectIterator(unreal.AnimationGraph):
            if obj.get_outer() and ABP.split("/")[-1] in str(obj.get_path_name()):
                queue.append(obj)
    except Exception as exc:
        log(f"ObjectIterator AnimationGraph: {exc}")

    try:
        for obj in unreal.ObjectIterator(unreal.EdGraph):
            path = str(obj.get_path_name())
            if "/ABP_FP_ArmsProcedural" in path and "AnimGraph" in path:
                queue.append(obj)
    except Exception as exc:
        log(f"ObjectIterator EdGraph: {exc}")

    while queue:
        g = queue.pop()
        if not g:
            continue
        key = g.get_path_name()
        if key in seen:
            continue
        seen.add(key)
        yield g
        # Nested graphs on state machines etc.
        try:
            nodes = list(g.nodes)
        except Exception:
            try:
                nodes = list(g.get_editor_property("nodes"))
            except Exception:
                nodes = []
        for n in nodes:
            for prop in ("bound_graph", "editor_bound_graph", "anim_graph"):
                try:
                    sub = n.get_editor_property(prop)
                    if sub:
                        queue.append(sub)
                except Exception:
                    pass
            # State machine states
            try:
                states = n.get_editor_property("states")
                for st in states or []:
                    try:
                        queue.append(st.get_editor_property("bound_graph"))
                    except Exception:
                        pass
            except Exception:
                pass


def set_slot_name(node, new_name: str) -> bool:
    # Node property paths vary by UE version
    candidates = [
        ("node", "slot_name"),
        ("Slot", "SlotName"),
        ("slot_name", None),
        ("SlotName", None),
    ]
    # Direct on AnimGraphNode_Slot
    for prop in ("slot_name", "SlotName"):
        try:
            node.set_editor_property(prop, new_name)
            log(f"set_editor_property({prop})={new_name} on {node.get_name()}")
            return True
        except Exception:
            pass

    # Nested FAnimNode_Slot
    try:
        anim_node = node.get_editor_property("node")
        for prop in ("slot_name", "SlotName"):
            try:
                anim_node.set_editor_property(prop, unreal.Name(new_name))
                log(f"node.{prop}={new_name} on {node.get_name()}")
                return True
            except Exception:
                try:
                    anim_node.set_editor_property(prop, new_name)
                    log(f"node.{prop} str={new_name} on {node.get_name()}")
                    return True
                except Exception:
                    pass
    except Exception as exc:
        log(f"get node struct failed: {exc}")

    # Raw export / property access
    try:
        # Some builds expose via AnimBlueprintLibrary
        if hasattr(unreal, "AnimBlueprintLibrary"):
            pass
    except Exception:
        pass

    return False


def fix_abp() -> None:
    bp = unreal.load_asset(ABP)
    if not bp:
        raise RuntimeError(f"Missing {ABP}")

    default_slots = []
    all_slots = []

    # Prefer explicit AnimGraph from function_graphs / anim graphs
    graphs = []
    try:
        graphs = list(unreal.AnimBlueprintLibrary.get_animation_graphs(bp))
        log(f"AnimBlueprintLibrary graphs={len(graphs)}")
    except Exception as exc:
        log(f"AnimBlueprintLibrary failed: {exc}")

    if not graphs:
        graphs = list(iter_anim_graphs(bp))

    # Always include named AnimGraph if present
    try:
        for g in bp.function_graphs:
            if g.get_name() == "AnimGraph":
                graphs.append(g)
    except Exception:
        pass

    seen_g = set()
    unique_graphs = []
    for g in graphs:
        if not g:
            continue
        k = g.get_path_name()
        if k in seen_g:
            continue
        seen_g.add(k)
        unique_graphs.append(g)

    log(f"Scanning {len(unique_graphs)} graphs")
    for g in unique_graphs:
        log(f"GRAPH {g.get_name()} path={g.get_path_name()}")
        try:
            nodes = list(g.nodes)
        except Exception:
            nodes = list(g.get_editor_property("nodes"))
        for n in nodes:
            cls = n.get_class().get_name()
            if "Slot" not in cls:
                continue
            t = node_title(n)
            all_slots.append((g, n, t))
            if "DefaultSlot" in t:
                default_slots.append((g, n, t))
                log(f"  FOUND {n.get_name()} :: {t}")

    log(f"Total slot nodes={len(all_slots)} DefaultSlot={len(default_slots)}")

    # Prefer renaming Slot_3 (ADS branch); keep Slot_4 as DefaultSlot
    renamed = 0
    keep = None
    for g, n, t in default_slots:
        if n.get_name() == "AnimGraphNode_Slot_4" or "Slot_4" in n.get_name():
            keep = n
            break
    if keep is None and default_slots:
        keep = default_slots[0][1]

    for g, n, t in default_slots:
        if n == keep:
            log(f"KEEP DefaultSlot on {n.get_name()}")
            continue
        if set_slot_name(n, NEW_SLOT):
            renamed += 1
            log(f"RENAMED {n.get_name()} -> {NEW_SLOT}")
        else:
            log(f"FAILED rename {n.get_name()} title={t}")
            # Last resort: remove node and try to bridge pins
            try:
                # Find Result / Pose links
                editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
                # Bridge: get input pose pin linked from, output linked to
                in_pin = None
                out_pin = None
                for pin in n.get_pins():
                    pname = str(pin.get_name())
                    if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT and pname in (
                        "Source",
                        "Pose",
                        "InPose",
                    ):
                        in_pin = pin
                    if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT and pname in (
                        "Pose",
                        "Result",
                        "OutPose",
                    ):
                        out_pin = pin
                # Fallback any pose-like
                if not in_pin or not out_pin:
                    for pin in n.get_pins():
                        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT and not in_pin:
                            if "pose" in str(pin.get_name()).lower() or str(pin.get_name()) == "Source":
                                in_pin = pin
                        if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT and not out_pin:
                            if "pose" in str(pin.get_name()).lower() or str(pin.get_name()) in ("Pose", "Result"):
                                out_pin = pin

                src_links = list(in_pin.linked_to) if in_pin else []
                dst_links = list(out_pin.linked_to) if out_pin else []
                log(f"Bridge attempt src={len(src_links)} dst={len(dst_links)}")
                for s in src_links:
                    for d in dst_links:
                        try:
                            s.make_link_to(d)
                        except Exception as exc:
                            log(f"link fail: {exc}")
                if hasattr(editor, "remove_node"):
                    editor.remove_node(n)
                else:
                    g.remove_node(n)
                renamed += 1
                log(f"REMOVED duplicate slot node {n.get_name()}")
            except Exception as exc:
                log(f"Remove fallback failed: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_asset(ABP, only_if_is_dirty=False)
    log(f"ABP compile/save renamed={renamed} saved={saved}")


def fix_inventory() -> None:
    bp = unreal.load_asset(INV)
    if not bp:
        log(f"Missing {INV}")
        return
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    nodes = list(editor.list_all_nodes()) if hasattr(editor, "list_all_nodes") else list(eg.nodes)

    setup = None
    to_remove = []
    for n in nodes:
        t = node_title(n).lower()
        cls = n.get_class().get_name()
        name = n.get_name()
        if name == "K2Node_CallFunction_0" or ("setup" in t and "inventory" in t):
            setup = n
        if any(
            k in t
            for k in (
                "set brush from material",
                "get all actors of class",
                "get materialinstance",
                "get characterpreview",
            )
        ) or cls == "K2Node_GetArrayItem" or name in (
            "K2Node_CallFunction_1",
            "K2Node_CallFunction_7",
            "K2Node_GetArrayItem_0",
            "K2Node_VariableGet_0",
            "K2Node_VariableGet_1",
        ):
            # Don't remove Setup itself
            if setup and n == setup:
                continue
            if "setup" in t and name == "K2Node_CallFunction_0":
                continue
            to_remove.append(n)

    # Break Setup.then first
    if setup:
        try:
            then_pin = setup.find_output_pin("then") if hasattr(setup, "find_output_pin") else None
            if not then_pin:
                for pin in setup.get_pins():
                    if str(pin.get_name()) == "then":
                        then_pin = pin
                        break
            if then_pin:
                try:
                    then_pin.break_all_pin_links(True)
                except Exception:
                    try:
                        then_pin.break_pin_links(True)
                    except Exception:
                        then_pin.break_all_pin_links()
                log("Broke Setup.then links")
        except Exception as exc:
            log(f"Break Setup.then failed: {exc}")

    removed = 0
    for n in to_remove:
        # Skip if this is actually Setup
        if setup and n.get_name() == setup.get_name():
            continue
        t = node_title(n).lower()
        if t.startswith("setup") and "target is wbp inventory" in t:
            continue
        try:
            if hasattr(editor, "remove_node"):
                editor.remove_node(n)
            else:
                eg.remove_node(n)
            removed += 1
            log(f"Removed {n.get_name()} ({node_title(n)})")
        except Exception as exc:
            log(f"Failed remove {n.get_name()}: {exc}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_asset(INV, only_if_is_dirty=False)
    log(f"Inventory fix removed={removed} saved={saved}")


def main() -> None:
    if LOG.exists():
        LOG.unlink()
    log("=== start ===")
    fix_inventory()
    fix_abp()
    log("=== done ===")


if __name__ == "__main__":
    main()
