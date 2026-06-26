"""Runtime test: spawn sniper, set ItemData HOLOSIGHT, call SpawnAttachments, check OpticSight."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_runtime_scope_test.log")
lines = []

sniper_cls = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper").generated_class()
pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
pickup_cdo = unreal.get_default_object(pickup.generated_class())

world = unreal.EditorLevelLibrary.get_editor_world()
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(sniper_cls, unreal.Vector(0, 0, 500), unreal.Rotator(0, 0, 0))

def optic_state(label):
    try:
        optic = actor.get_editor_property("OpticSight")
        sm = optic.get_editor_property("static_mesh") if optic else None
        lines.append(f"{label}: OpticSight mesh={sm.get_name() if sm else None} hidden={optic.get_editor_property('hidden_in_game')}")
    except Exception as exc:
        lines.append(f"{label}: ERR {exc}")

optic_state("after_spawn")

# copy ItemData from pickup
try:
  item_data = pickup_cdo.get_editor_property("ItemData")
  actor.set_editor_property("ItemData", item_data)
  lines.append(f"set ItemData sight={pickup_cdo.get_editor_property('Item Data AttachmentsSight')}")
except Exception as exc:
  lines.append(f"ItemData ERR {exc}")

optic_state("after_itemdata")

# call SetWeaponAmmoData
try:
    actor.set_weapon_ammo_data(True)
    lines.append("called set_weapon_ammo_data(True)")
except Exception as exc:
    lines.append(f"set_weapon_ammo_data ERR {exc}")

optic_state("after_setweaponammo")

# call SpawnAttachments
try:
    actor.spawn_attachments()
    lines.append("called spawn_attachments()")
except Exception as exc:
    lines.append(f"spawn_attachments ERR {exc}")

optic_state("after_spawnattachments")

# BeginPlay already ran - try SetStaticMesh manually via ScopeSightMesh
try:
    scope_mesh = actor.get_editor_property("ScopeSightMesh")
    optic = actor.get_editor_property("OpticSight")
    if scope_mesh and optic:
        optic.set_static_mesh(scope_mesh)
        optic.set_visibility(True, False)
        lines.append(f"manual set_static_mesh({scope_mesh.get_name()})")
except Exception as exc:
    lines.append(f"manual ERR {exc}")

optic_state("after_manual")

# list all static mesh comps
for comp in actor.get_components_by_class(unreal.StaticMeshComponent.static_class()):
    sm = comp.get_editor_property("static_mesh")
    if sm:
        lines.append(f"  COMP {comp.get_name()} -> {sm.get_name()}")

unreal.EditorLevelLibrary.destroy_actor(actor)
OUT.write_text("\n".join(lines))
