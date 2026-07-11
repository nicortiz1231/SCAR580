"""Check BP_FPCharacter for SCAR laser-related components."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_fpcharacter_components.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
if not bp:
    lines.append("MISSING BP_FPCharacter")
else:
    for comp_name in (
        "SCARWeaponAttachmentComponent",
        "SCARSniperAdsCameraComponent",
        "SCARArLaserPresentationComponent",
    ):
        has = False
        try:
            has = any(
                str(c.get_name()).endswith(comp_name) or comp_name in str(c.get_class())
                for c in unreal.BlueprintEditorLibrary.get_blueprint_components(bp)
            )
        except Exception:
            for obj in bp.get_editor_property("component_templates") or []:
                if comp_name in str(obj.get_class()):
                    has = True
        lines.append(f"{comp_name}: {has}")

OUT.write_text("\n".join(lines))
