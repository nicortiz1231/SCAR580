import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_ac_bodycam.log")
lines = []


def p(msg):
    lines.append(str(msg))


bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Components/AC_BodycamCamera.AC_BodycamCamera")
generated = bp.generated_class()
cdo = unreal.get_default_object(generated)
p(f"class={generated.get_name()} cdo_type={type(cdo)} cdo_class={cdo.get_class().get_name()}")

for name in sorted(dir(cdo)):
    if name.startswith("_"):
        continue
    if any(k in name.lower() for k in ("camera", "post", "light", "mesh", "visible", "hidden", "component")):
        try:
            val = cdo.get_editor_property(name)
            p(f"{name}={val}")
        except Exception as exc:
            p(f"{name}: {exc}")

LOG.write_text("\n".join(lines))
