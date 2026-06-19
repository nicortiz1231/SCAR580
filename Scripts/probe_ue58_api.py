"""Probe UE 5.8 Python APIs for blueprint/material editing."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ue58_api.log")
lines = []

def p(msg):
    lines.append(str(msg))
    unreal.log(str(msg))

BP_ASSET = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
M_VIGNETTE = "/Game/BodycamFPSKIT/Blueprints/Camera/Materials/M_Vignette"

bp = unreal.load_asset(BP_ASSET)
mat = unreal.load_asset(M_VIGNETTE)

p(f"BP type {type(bp)}")
for name in ("simple_construction_script", "SimpleConstructionScript"):
    try:
        p(f"{name} = {bp.get_editor_property(name)}")
    except Exception as exc:
        p(f"{name} ERR {exc}")

for fn in dir(unreal.BlueprintEditorLibrary):
    if "component" in fn.lower() or "construction" in fn.lower():
        p(f"BEL {fn}")

try:
    nodes = unreal.BlueprintEditorLibrary.get_blueprint_component_node_names(bp)
    p(f"node names {list(nodes)}")
except Exception as exc:
    p(f"node names ERR {exc}")

p(f"mat blend {mat.get_editor_property('blend_mode')}")
p(f"mat domain {mat.get_editor_property('material_domain')}")

OUT.write_text("\n".join(lines))
