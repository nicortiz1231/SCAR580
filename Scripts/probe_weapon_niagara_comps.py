"""List Niagara components on weapon/item CDO."""
import unreal

for path in (
    "/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base",
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Pistol/BP_Weapon_Pistol.BP_Weapon_Pistol",
    "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter",
):
    bp = unreal.load_asset(path)
    if not bp:
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    unreal.log(f"=== {path} ===")
    for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
        cn = comp.get_name()
        cls = comp.get_class().get_name()
        if "Niagara" in cls or "Casing" in cn or "Bullet" in cn or "Shell" in cn:
            asset = ""
            try:
                asset = str(comp.get_editor_property("asset"))
            except Exception:
                pass
            unreal.log(f"  {cn} | {cls} | asset={asset}")
