"""Find sight/scope logic anywhere in Bodycam item + sniper blueprints."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sight_logic_all.log")
lines = []

KEYWORDS = (
    "Sight", "Scope", "Optic", "HOLO", "ENUM_Sights", "ChangeSight",
    "SetStaticMesh", "4xScope", "SpareMag",
)

def scan_bp(label, path):
    bp = unreal.load_asset(path)
    if not bp:
        lines.append(f"MISSING {path}")
        return
    lines.append(f"\n######## {label} ########")
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        hits = []
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            if any(k.lower() in title.lower() for k in KEYWORDS):
                hits.append(f"  {node.get_name()} | {title}")
        if hits:
            lines.append(f"[{g.get_name()}] ({len(hits)} hits)")
            lines.extend(hits)

    cdo = unreal.get_default_object(bp.generated_class())
    for prop in ("ScopeSightMesh", "OpticSightMesh", "SpareMagMesh"):
        try:
            val = cdo.get_editor_property(prop)
            lines.append(f"  CDO {prop}={val.get_path_name() if val else None}")
        except Exception:
            pass

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        )
        if not obj or obj.get_class().get_name() != "StaticMeshComponent":
            continue
        if "Optic" not in obj.get_name() and "Sight" not in obj.get_name():
            continue
        sm = obj.get_editor_property("static_mesh")
        lines.append(f"  SCS {obj.get_name()} static_mesh={sm.get_path_name() if sm else None} hidden={obj.get_editor_property('hidden_in_game')}")

scan_bp("item", "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
scan_bp("sniper", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
scan_bp("pickup", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")

# char wheel spawn full chain from SetAmmo 212
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
ced = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char))
lines.append("\n######## CHAR spawn chain from SetAmmo 212 ########")
node212 = next(n for n in ced.list_all_nodes() if n.get_name() == "K2Node_CallFunction_212")
then = node212.find_output_pin("then")
stack = [then]
depth = 0
while stack and depth < 20:
    pin = stack.pop()
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        if lp.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT:
            continue
        o = lp.get_owning_node()
        lines.append(f"  {o.get_name()} | {str(o.get_node_title()).replace(chr(10),' | ')}")
        nxt = o.find_output_pin("then")
        if nxt:
            stack.append(nxt)
        depth += 1

# rogue char scope nodes
lines.append("\n######## CHAR custom scope nodes ########")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in ed.list_all_nodes():
        title = str(node.get_node_title())
        if "SetStaticMesh" in title or "ScopeSightMesh" in title or "4xScope" in title:
            lines.append(f"[{g.get_name()}] {node.get_name()} | {title.replace(chr(10),' ')}")

OUT.write_text("\n".join(lines))
