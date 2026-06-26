"""Full UserConstructionScript + AimDownSight + item EventGraph SpawnAttachments in ORIGINAL."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_orig_ucs_aimdown.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")

for gname in ("UserConstructionScript", "AimDownSight", "EventGraph"):
    for g in unreal.BlueprintEditorLibrary.list_graphs(item):
        if g.get_name() != gname:
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        lines.append(f"\n=== {gname} ({len(ed.list_all_nodes())} nodes) FULL ===")
        for node in ed.list_all_nodes():
            title = str(node.get_node_title()).replace("\n", " | ")
            lines.append(f"  {node.get_name()} | {title}")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                linked = [f"{lp.get_owning_node().get_name()}:{unreal.BlueprintGraphPinLibrary.get_pin_name(lp)}" for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin)]
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if linked or (val and pn not in ("execute",)):
                    lines.append(f"    {pn} -> {linked or val}")

# Spawn sniper CDO and check runtime components
sniper_cls = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper").generated_class()
world = unreal.EditorLevelLibrary.get_editor_world()
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(sniper_cls, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))
lines.append(f"\n=== SPAWNED sniper in editor world ===")
try:
    optic = actor.get_editor_property("OpticSight")
    sm = optic.get_editor_property("static_mesh") if optic else None
    lines.append(f"  OpticSight static_mesh={sm.get_name() if sm else None}")
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent.static_class()):
        sm2 = comp.get_editor_property("static_mesh")
        if sm2 and ("Scope" in sm2.get_name() or "Sight" in sm2.get_name()):
            lines.append(f"  {comp.get_name()} mesh={sm2.get_name()} hidden={comp.get_editor_property('hidden_in_game')}")
except Exception as exc:
    lines.append(f"  ERR {exc}")
unreal.EditorLevelLibrary.destroy_actor(actor)

OUT.write_text("\n".join(lines))
