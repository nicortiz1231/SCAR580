"""Probe sniper scope visibility chain and recoil/camera clip settings."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_scope_recoil_state.log")
lines = []


def pin_links(node, pin_name):
    pin = node.find_output_pin(pin_name) or node.find_input_pin(pin_name)
    if not pin:
        return []
    out = []
    for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
        o = lp.get_owning_node()
        out.append(f"{o.get_name()} | {str(o.get_node_title()).replace(chr(10), ' | ')}")
    return out


SNIPER = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"
ITEM = "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base"
CHAR = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"

sniper_bp = unreal.load_asset(SNIPER)
item_bp = unreal.load_asset(ITEM)
char_bp = unreal.load_asset(CHAR)

cdo = unreal.get_default_object(sniper_bp.generated_class())
lines.append("=== Sniper CDO ===")
for prop in ("ScopeSightMesh", "OpticSightMesh", "AimDistanceFromCamera", "ProceduralValues"):
    try:
        val = cdo.get_editor_property(prop)
        lines.append(f"  {prop}={val.get_name() if hasattr(val, 'get_name') else val!r}")
    except Exception as exc:
        lines.append(f"  {prop} ERR {exc}")

try:
    optic = cdo.get_editor_property("OpticSight")
    sm = optic.get_editor_property("static_mesh") if optic else None
    hidden = optic.get_editor_property("hidden_in_game") if optic else None
    vis = optic.get_editor_property("visible") if optic else None
    lines.append(f"  OpticSight.static_mesh={sm.get_name() if sm else None}")
    lines.append(f"  OpticSight.hidden_in_game={hidden} visible={vis}")
except Exception as exc:
    lines.append(f"  OpticSight ERR {exc}")

# all sniper static mesh components
try:
    for comp in cdo.get_components_by_class(unreal.StaticMeshComponent.static_class()):
        sm = comp.get_editor_property("static_mesh")
        lines.append(
            f"  comp {comp.get_name()} mesh={sm.get_name() if sm else None} "
            f"hidden={comp.get_editor_property('hidden_in_game')}"
        )
except Exception as exc:
    lines.append(f"  comps ERR {exc}")

lines.append("=== Sniper graphs (scope/visibility) ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(sniper_bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if not any(k in title for k in ("SetStaticMesh", "SetVisibility", "SpawnAttachment", "OpticSight", "ScopeSight")):
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()} | {title}")
        for pn in ("execute", "then", "self", "NewMesh", "bNewVisibility"):
            links = pin_links(node, pn)
            if links:
                lines.append(f"  {pn} -> {links}")

lines.append("=== Item SpawnAttachments event ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(item_bp):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if "SpawnAttachments" not in str(node.get_node_title()):
            continue
        lines.append(f"[{g.get_name()}] {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")
        then = pin_links(node, "then")
        if then:
            lines.append(f"  then -> {then}")

lines.append("=== Item Akimbo Spawner sight nodes ===")
for g in unreal.BlueprintEditorLibrary.list_graphs(item_bp):
    if g.get_name() != "Akimbo Spawner":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        title = str(node.get_node_title()).replace("\n", " | ")
        if any(k in title for k in ("Switch on ENUM_Sights", "SetStaticMesh", "SetVisibility", "OpticSight", "ScopeSight")):
            lines.append(f"  {node.get_name()} | {title}")

lines.append("=== Character sight switches ===")
eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(char_bp))
for node in eg.list_all_nodes():
    if "Switch on ENUM_Sights" not in str(node.get_node_title()):
        continue
    lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")
    for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
        if not pn.startswith("NewEnumerator"):
            continue
        links = pin_links(node, pn)
        if links:
            lines.append(f"    {pn} -> {links}")

# procedural recoil values
dt = cdo.get_editor_property("ProceduralValues")
lines.append("=== Sniper ProceduralValues ===")
if dt:
    for prop in ("WeaponValues", "RecoilValues", "ADS_Speed", "ADS_Alpha"):
        try:
            val = dt.get_editor_property(prop)
            lines.append(f"  {prop}={val!r}")
            if hasattr(val, "get_editor_property"):
                for sub in sorted(dir(val)):
                    if sub.startswith("_"):
                        continue
                    sub_lower = sub.lower()
                    if any(k in sub_lower for k in ("recoil", "kick", "loc", "rot", "offset", "back", "pose", "aim")):
                        try:
                            sv = val.get_editor_property(sub)
                            lines.append(f"    {sub}={sv!r}")
                        except Exception:
                            pass
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

# camera
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in sds.k2_gather_subobject_data_for_blueprint(char_bp):
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if not obj or "FirstPersonCamera" not in obj.get_name():
        continue
    lines.append(f"=== {obj.get_name()} ===")
    for prop in ("near_clip_plane", "NearClipPlane", "field_of_view"):
        try:
            lines.append(f"  {prop}={obj.get_editor_property(prop)!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")

OUT.write_text("\n".join(lines))
