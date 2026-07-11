"""Dump all IMC_Player_Default mappings."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_imc_all_keys.log")
lines = []

for path in ("/Game/BodycamFPSKIT/Input/IMC_Player", "/Game/BodycamFPSKIT/Input/IMC_Player_Default"):
    imc = unreal.load_asset(f"{path}.{path.split('/')[-1]}")
    if not imc:
        continue
    lines.append(f"=== {path} ===")
    dkm = imc.get_editor_property("default_key_mappings")
    mappings = dkm.get_editor_property("mappings")
    for mapping in mappings:
        action = mapping.get_editor_property("action")
        key = mapping.get_editor_property("key")
        an = action.get_name() if action else "?"
        kn = str(key.get_editor_property("key_name")) if key else "?"
        lines.append(f"  {kn} -> {an}")

OUT.write_text("\n".join(lines))
