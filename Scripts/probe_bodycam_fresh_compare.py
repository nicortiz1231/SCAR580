"""Compare original BODYCAMFPSKIT sniper equip flow vs SCAR — run after full restore."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_fresh_compare.log")
lines = []


def w(s=""):
    lines.append(s)


def pin_info(node, names):
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if pn not in names:
            continue
        linked = []
        for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
            o = lp.get_owning_node()
            linked.append(f"{o.get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}")
        val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
        if linked or val:
            w(f"    {pn} -> {linked or val}")


def dump_item_spawnattachments():
    item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
    for g in unreal.BlueprintEditorLibrary.list_graphs(item):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if "SpawnAttachments" not in title and "SpawnAttachment" not in title:
                continue
            if node.get_class().get_name() not in ("K2Node_CustomEvent", "K2Node_CallFunction", "K2Node_FunctionEntry"):
                if "SpawnAttachment" not in title:
                    continue
            w(f"[ITEM/{g.get_name()}] {node.get_name()} | {title}")
            pin_info(node, ("execute", "then", "self", "Selection", "Sight", "NewMesh"))

    # trace SpawnAttachments custom event body
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
    spawn_ev = None
    for node in eg.list_all_nodes():
        if node.get_class().get_name() == "K2Node_CustomEvent" and "SpawnAttachments" in str(node.get_node_title()):
            spawn_ev = node
            break
    if spawn_ev:
        w("=== SpawnAttachments event body ===")
        then = spawn_ev.find_output_pin("then")
        visited = set()
        stack = [then]
        depth = 0
        while stack and depth < 40:
            pin = stack.pop()
            if not pin:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                o = lp.get_owning_node()
                if id(o) in visited:
                    continue
                visited.add(id(o))
                t = str(o.get_node_title()).replace("\n", " | ")
                w(f"  {o.get_name()} | {t}")
                nxt = o.find_output_pin("then")
                if nxt:
                    stack.append(nxt)


def dump_pickup_vs_weapon():
    for label, path in (
        ("pickup", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"),
        ("weapon", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"),
    ):
        asset = unreal.load_asset(path)
        cdo = unreal.get_default_object(asset.generated_class())
        w(f"=== {label} CDO ===")
        for prop in (
            "ScopeSightMesh", "OpticSightMesh", "AimDistanceFromCamera",
            "Item Data AttachmentsSight", "Item Data AttachmentsLaser",
            "Item Data AttachmentsMuzzle", "Item Data Ammo Count", "Item Data Max Ammo",
        ):
            try:
                val = cdo.get_editor_property(prop)
                if hasattr(val, "get_path_name"):
                    val = val.get_path_name()
                w(f"  {prop}={val!r}")
            except Exception as exc:
                w(f"  {prop} ERR {exc}")


def dump_char_spawn_chain():
    char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
    ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
    targets = (
        "K2Node_SpawnActorFromClass_1", "K2Node_CallFunction_157", "K2Node_CallFunction_212",
        "K2Node_CallFunction_141", "K2Node_CallFunction_140", "K2Node_CallFunction_46",
        "K2Node_CallFunction_17",
    )
    for name in targets:
        for node in ed.list_all_nodes():
            if node.get_name() != name:
                continue
            w(f"=== CHAR {name} | {str(node.get_node_title()).replace(chr(10),' | ')} ===")
            pin_info(node, ("execute", "then", "self", "Class", "ItemData"))

    # HandsSlot
    for g in unreal.BlueprintEditorLibrary.list_graphs(char):
        if g.get_name() != "BeginSetup":
            continue
        ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ged.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            w("=== HandsSlot ItemData ===")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val and ("ItemData" in pn or "Attachments" in pn):
                    w(f"  {pn}={val}")

    # count rogue scope nodes on character
    scope_nodes = []
    for g in unreal.BlueprintEditorLibrary.list_graphs(char):
        ged = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ged.list_all_nodes():
            title = str(node.get_node_title())
            if "SetStaticMesh" in title or "ScopeSightMesh" in title:
                mesh_pin = node.find_input_pin("NewMesh") if hasattr(node, "find_input_pin") else None
                val = ""
                if mesh_pin:
                    val = str(unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin))
                scope_nodes.append(f"[{g.get_name()}] {node.get_name()} | {title.replace(chr(10),' ')} | mesh={val}")
    w(f"=== Character scope-related nodes ({len(scope_nodes)}) ===")
    for n in scope_nodes:
        w(f"  {n}")


def dump_sniper_graphs():
    sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
    for gname in ("EventGraph", "UserConstructionScript"):
        g = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(sniper) if g.get_name() == gname), None)
        if not g:
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        w(f"=== Sniper {gname} nodes ===")
        for node in ed.list_all_nodes():
            w(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")


dump_item_spawnattachments()
dump_pickup_vs_weapon()
dump_char_spawn_chain()
dump_sniper_graphs()
OUT.write_text("\n".join(lines))
