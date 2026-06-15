import unreal

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
cdo = unreal.get_default_object(bp.generated_class())
print("component count", len(cdo.get_components_by_class(unreal.ActorComponent.static_class())))
for comp in cdo.get_components_by_class(unreal.ActorComponent.static_class()):
    print(comp.get_name(), comp.get_class().get_name())
print("BODYCAM", cdo.get_editor_property("BODYCAM"))
