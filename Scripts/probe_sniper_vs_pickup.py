"""Compare sniper current state vs pickup (Map_Test reference)."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_vs_pickup.log")
lines = []


def dump_cdo(label, path, props):
    asset = unreal.load_asset(path)
    if not asset:
        lines.append(f"MISSING {path}")
        return
    cdo = unreal.get_default_object(asset.generated_class())
    lines.append(f"=== {label} ===")
    for prop in props:
        try:
            val = cdo.get_editor_property(prop)
            if hasattr(val, "get_path_name"):
                val = val.get_path_name()
            lines.append(f"  {prop}={val!r}")
        except Exception as exc:
            lines.append(f"  {prop} ERR {exc}")


NUMERIC_PROPS = (
    "AimDistanceFromCamera",
    "ChangeSightSpeed",
    "ScopeMat_SightDistance",
    "ScopeMat_GradientParam",
)
MESH_PROPS = ("ScopeSightMesh", "OpticSightMesh", "ProceduralValues")
ATTACH_PROPS = (
    "Item Data AttachmentsSight",
    "Item Data AttachmentsLaser",
    "Item Data AttachmentsMuzzle",
    "Item Data Attachments Grip",
    "Item Data Ammo Count",
    "Item Data Max Ammo",
)

for label, path in (
    ("pickup", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"),
    ("weapon", "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"),
):
    dump_cdo(label, path, ATTACH_PROPS + NUMERIC_PROPS + MESH_PROPS)

# HandsSlot construct in character
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if graph.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        lines.append("=== HandsSlot construct pins ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
            if val:
                lines.append(f"  {pname}={val}")

# DT sniper animation values row
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
cdo = unreal.get_default_object(sniper.generated_class())
pv = cdo.get_editor_property("ProceduralValues")
if pv:
    lines.append(f"=== ProceduralValues DT={pv.get_path_name()} ===")
    try:
        wv = pv.get_editor_property("WeaponValues")
        loc = wv.get_editor_property("BasePoseLoc")
        rot = wv.get_editor_property("BasePoseRot")
        lines.append(f"  BasePoseLoc=({loc.x},{loc.y},{loc.z})")
        lines.append(f"  BasePoseRot=({rot.roll},{rot.pitch},{rot.yaw})")
    except Exception as exc:
        lines.append(f"  WeaponValues ERR {exc}")
    try:
        rv = pv.get_editor_property("RecoilValues")
        for prop in ("RecoilLoc", "RecoilRot", "RecoilTranslation", "RecoilRotation"):
            try:
                val = rv.get_editor_property(prop)
                if hasattr(val, "x"):
                    lines.append(f"  RecoilValues.{prop}=({val.x},{val.y},{val.z})")
            except Exception:
                pass
    except Exception as exc:
        lines.append(f"  RecoilValues ERR {exc}")

# Item base SpawnAttachments custom wiring
item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
ied = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(item))
lines.append("=== Item SpawnAttachments graph nodes ===")
for node in ied.list_all_nodes():
    if "SpawnAttachments" not in str(node.get_node_title()) and node.get_class().get_name() != "K2Node_CustomEvent":
        continue
    title = str(node.get_node_title()).replace("\n", " | ")
    if "SpawnAttachments" in title or node.get_class().get_name() == "K2Node_CustomEvent":
        lines.append(f"  {node.get_name()} | {title}")

# Sniper extra scope nodes count
for gname in ("EventGraph", "UserConstructionScript"):
    graph = next((g for g in unreal.BlueprintEditorLibrary.list_graphs(sniper) if g.get_name() == gname), None)
    if not graph:
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    scope_nodes = []
    for node in editor.list_all_nodes():
        title = str(node.get_node_title())
        if "SetStaticMesh" in title or "SetVisibility" in title:
            scope_nodes.append(f"{node.get_name()}|{title.replace(chr(10),' ')}")
    lines.append(f"=== Sniper {gname} mesh nodes ({len(scope_nodes)}) ===")
    for n in scope_nodes:
        lines.append(f"  {n}")

OUT.write_text("\n".join(lines))
