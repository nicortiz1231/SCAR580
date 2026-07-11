"""Find pistol/handgun weapon blueprints and their parent class."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_handgun_class.log")
lines = []

registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = registry.get_assets_by_path("/Game/BodycamFPSKIT/Blueprints/Interactables", recursive=True)
for data in assets:
    name = str(data.asset_name)
    if any(k in name.lower() for k in ("pistol", "handgun", "glock", "gun", "weapon")):
        obj = data.get_asset()
        if not obj:
            continue
        cls = obj.generated_class() if hasattr(obj, "generated_class") else None
        parent = cls.get_super_class().get_name() if cls else "?"
        lines.append(f"{data.package_name} parent={parent}")

OUT.write_text("\n".join(lines))
