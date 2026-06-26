"""Deep probe: sniper BeginPlay chain, SpawnAttachments override, item sight logic."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_scope_deep.log")
lines = []

SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"


def dump_exec_chain(editor, start_node, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 12 or id(start_node) in seen:
        return
    seen.add(id(start_node))
    title = str(start_node.get_node_title()).replace("\n", " | ")
    lines.append(f"{'  '*depth}{start_node.get_name()} | {title}")
    then = start_node.find_output_pin("then") or start_node.find_output_pin("Then")
    if not then:
        return
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        dump_exec_chain(editor, lp.get_owning_node(), depth + 1, seen)


def dump_node_pins(node, names):
    for pn in names:
        pin = node.find_input_pin(pn) or node.find_output_pin(pn)
        if not pin:
            continue
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")
        lines.append(f"  {pn}: val={val!r} linked={linked}")


sniper_bp = unreal.load_asset(SNIPER)
item_bp = unreal.load_asset(ITEM)

lines.append("=== Sniper BeginPlay exec chain ===")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper_bp))
begin = eg.find_event_node("ReceiveBeginPlay")
if begin:
    dump_exec_chain(eg, begin)

lines.append("=== Sniper SpawnAttachments events ===")
for node in eg.list_all_nodes():
    if "SpawnAttachments" not in str(node.get_node_title()):
        continue
    lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")
    dump_exec_chain(eg, node)

lines.append("=== Sniper SetStaticMesh nodes detail ===")
for node in eg.list_all_nodes():
    if "SetStaticMesh" not in str(node.get_node_title()):
        continue
    lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")
    dump_node_pins(node, ("execute", "then", "self", "NewMesh"))

ucs = None
for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
    if g.get_name() == "UserConstructionScript":
        ucs = unreal.BlueprintGraphEditor.get_graph_editor(g)
        break
if ucs:
    lines.append("=== Sniper UCS SetStaticMesh detail ===")
    for node in ucs.list_all_nodes():
        if "SetStaticMesh" not in str(node.get_node_title()):
            continue
        lines.append(f"{node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")
        dump_node_pins(node, ("execute", "then", "self", "NewMesh"))

# Item base - all graphs with ENUM_Sights switch
lines.append("=== Item ENUM_Sights switches ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(item_bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if "Switch on ENUM_Sights" not in str(node.get_node_title()):
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()}")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if not pn.startswith("NewEnumerator"):
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                lines.append(f"  {pn} -> {o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")

# subobject OpticSight template via subsystem
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lines.append("=== Sniper OpticSight subobjects ===")
for handle in sds.k2_gather_subobject_data_for_blueprint(sniper_bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "OpticSight" not in obj.get_name():
        continue
    sm = None
    try:
        sm = obj.get_editor_property("static_mesh")
    except Exception:
        pass
    lines.append(
        f"  {obj.get_name()} class={obj.get_class().get_name()} "
        f"mesh={sm.get_name() if sm else None}"
    )

OUT.write_text("\n".join(lines))
