"""Probe body mesh anim class, its variables, and body skeleton weapon sockets."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_avatar_anim_setup.log")
lines = []


def log(msg):
    lines.append(str(msg))


def dump_sockets(mesh, label):
    names = []
    try:
        for sock in mesh.get_editor_property("sockets"):
            names.append(str(sock.get_editor_property("socket_name")))
    except Exception as exc:
        log(f"  mesh sockets err: {exc}")
    skel = mesh.get_editor_property("skeleton")
    if skel:
        try:
            for sock in skel.get_editor_property("sockets"):
                names.append(str(sock.get_editor_property("socket_name")))
        except Exception as exc:
            log(f"  skel sockets err: {exc}")
    log(f"  {label} sockets: {sorted(set(names))}")


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
gen_class = unreal.load_object(None, bp.get_path_name() + "_C")
cdo = unreal.get_default_object(gen_class)

abp_assets = {}

for comp in cdo.get_components_by_class(unreal.SkeletalMeshComponent.static_class()):
    name = comp.get_name()
    mesh = comp.get_editor_property("skeletal_mesh_asset")
    anim_class = comp.get_editor_property("anim_class")
    log(f"=== component {name} ===")
    log(f"  mesh={mesh.get_path_name() if mesh else None}")
    log(f"  anim_class={anim_class.get_path_name() if anim_class else None}")
    try:
        log(f"  attach_parent={comp.get_attach_parent()}")
        log(f"  attach_socket={comp.get_attach_socket_name()}")
    except Exception as exc:
        log(f"  attach info err: {exc}")
    if mesh:
        dump_sockets(mesh, name)
    if anim_class:
        class_path = anim_class.get_path_name()
        asset_path = class_path.rsplit(".", 1)[0]
        asset_name = asset_path.rsplit("/", 1)[-1]
        abp_assets[asset_name] = f"{asset_path}.{asset_name}"

for asset_name, full_path in abp_assets.items():
    abp = unreal.load_asset(full_path)
    if not abp:
        log(f"=== could not load anim BP {full_path} ===")
        continue
    log(f"=== anim BP {asset_name} variables ===")
    try:
        for nv in abp.get_editor_property("new_variables"):
            vname = nv.get_editor_property("var_name")
            vtype = nv.get_editor_property("var_type")
            cat = vtype.get_editor_property("pin_category")
            sub = vtype.get_editor_property("pin_sub_category_object")
            subname = sub.get_name() if sub else ""
            log(f"  var: {vname} ({cat} {subname})")
    except Exception as exc:
        log(f"  new_variables err: {exc}")

OUT.write_text("\n".join(lines))
print("probe complete")
