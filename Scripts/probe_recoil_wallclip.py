"""Probe AC_ProceduralRecoil and Wall Clip on character."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_recoil_wallclip.log")
lines = []

ac = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_ProceduralRecoil.AC_ProceduralRecoil")
cdo = unreal.get_default_object(ac.generated_class())
lines.append(f"AC_ProceduralRecoil={cdo.get_class().get_name()}")
for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    lower = name.lower()
    if not any(k in lower for k in ("recoil", "kick", "back", "loc", "rot", "strength", "amount", "clip", "wall")):
        continue
    try:
        lines.append(f"  {name}={cdo.get_editor_property(name)!r}")
    except Exception:
        pass

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() != "Wall Clip":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== Wall Clip graph ({len(editor.list_all_nodes())} nodes) ===")
    for node in editor.list_all_nodes()[:20]:
        lines.append(f"  {node.get_name()} | {str(node.get_node_title()).replace(chr(10), ' | ')}")

# sniper WeaponValues known fields
sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
pv = unreal.get_default_object(sniper.generated_class()).get_editor_property("ProceduralValues")
wv = pv.get_editor_property("WeaponValues")
for name in sorted(dir(wv)):
    if name.startswith("_"):
        continue
    try:
        lines.append(f"  wv.{name}={wv.get_editor_property(name)!r}")
    except Exception:
        pass

OUT.write_text("\n".join(lines))
