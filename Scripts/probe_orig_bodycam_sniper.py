"""Probe original BODYCAMFPSKIT sniper - run against original uproject."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_bodycam_sniper.log")
lines = []

sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
if not sniper:
    OUT.write_text("MISSING")
else:
    cdo = unreal.get_default_object(sniper.generated_class())
    lines.append("=== ORIGINAL sniper CDO ===")
    for prop in ("AimDistanceFromCamera", "OpticSightMesh", "ScopeSightMesh"):
        v = cdo.get_editor_property(prop)
        lines.append(f"  {prop}={v.get_path_name() if hasattr(v, 'get_path_name') else v}")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(sniper):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or "OpticSight" not in obj.get_name():
            continue
        if obj.get_class().get_name() != "StaticMeshComponent":
            continue
        sm = obj.get_editor_property("static_mesh")
        lines.append(f"  OpticSight template mesh={sm.get_path_name() if sm else None}")

    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(sniper))
    lines.append(f"=== EventGraph {len(eg.list_all_nodes())} nodes ===")
    for node in eg.list_all_nodes():
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10),' | ')}")

    # item base SpawnAttachments
    item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
    ieg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
    for node in ieg.list_all_nodes():
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        lines.append("=== ITEM SpawnAttachments chain ===")
        then = node.find_output_pin("then")
        stack = [(then, 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 20:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
                    continue
                o = lp.get_owning_node()
                lines.append(f"{'  '*depth}{o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
                nxt = o.find_output_pin("then")
                if nxt:
                    stack.append((nxt, depth + 1))

    # ALL SetStaticMesh on OpticSight across item graphs
    lines.append("=== ALL item SetStaticMesh on OpticSight ===")
    for g in unreal.BlueprintEditorLibrary.list_graphs(item):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            if "SetStaticMesh" not in str(node.get_node_title()):
                continue
            self_pin = node.find_input_pin("self")
            mesh_pin = node.find_input_pin("NewMesh")
            self_l = mesh_l = val = ""
            if self_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(self_pin):
                    self_l = str(lp.get_owning_node().get_node_title())
            if mesh_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(mesh_pin):
                    mesh_l = str(lp.get_owning_node().get_node_title())
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin)
            if "Optic" in self_l or "Scope" in mesh_l or "Scope" in val or "4x" in val:
                lines.append(f"  [{g.get_name()}] {node.get_name()} self={self_l} mesh={mesh_l or val}")

    OUT.write_text("\n".join(lines))
