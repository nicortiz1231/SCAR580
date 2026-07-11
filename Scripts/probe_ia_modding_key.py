"""Find IA_Modding key binding in IMC."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ia_modding_key.log")
lines = []

for imc_path in (
    "/Game/BodycamFPSKIT/Input/IMC_Player",
    "/Game/BodycamFPSKIT/Input/IMC_Player_Default",
):
    imc = unreal.load_asset(f"{imc_path}.{imc_path.split('/')[-1]}")
    if not imc:
        continue
    lines.append(f"=== {imc_path} ===")
    mappings = imc.get_editor_property("mappings")
    for m in mappings:
        action = m.get_editor_property("action")
        aname = action.get_name() if action else "?"
        keys = []
        for i in range(10):
            try:
                k = m.get_editor_property(f"key_{i}") if hasattr(m, f"key_{i}") else None
            except Exception:
                k = None
        # EnhancedInputActionMappingData
        for prop in ("key", "triggers", "modifiers"):
            try:
                val = m.get_editor_property(prop)
                if val:
                    lines.append(f"  action={aname} {prop}={val}")
            except Exception:
                pass
        try:
            key = m.get_editor_property("key")
            lines.append(f"  action={aname} key={key}")
        except Exception as exc:
            lines.append(f"  action={aname} key ERR {exc}")

ia = unreal.load_asset("/Game/BodycamFPSKIT/Input/Actions/IA_Modding.IA_Modding")
lines.append(f"IA_Modding={ia}")

OUT.write_text("\n".join(lines))
