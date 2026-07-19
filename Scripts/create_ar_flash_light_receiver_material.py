"""Create /Game/SCAR580/Materials/M_AR_FlashLightReceiver.

Additive DefaultLit white plane so SpotLight + M_Light (exact horror-kit flashlight)
can project onto it. Unlit pixels add nothing over AR passthrough; lit pixels show the cookie.
"""
import unreal

ASSET_PATH = "/Game/SCAR580/Materials"
ASSET_NAME = "M_AR_FlashLightReceiver"
FULL_PATH = f"{ASSET_PATH}/{ASSET_NAME}"


def main() -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(FULL_PATH):
        material = unreal.load_asset(FULL_PATH)
        unreal.log(f"[create_ar_flash_receiver] exists, updating: {FULL_PATH}")
    else:
        unreal.EditorAssetLibrary.make_directory(ASSET_PATH)
        factory = unreal.MaterialFactoryNew()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(ASSET_NAME, ASSET_PATH, unreal.Material, factory)
        if not material:
            raise RuntimeError("Failed to create material asset")

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    material.set_editor_property("two_sided", True)

    # Clear old expressions if re-running.
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -350, 0
    )
    base.set_editor_property("constant", unreal.LinearColor(1.0, 1.0, 0.97, 1.0))

    roughness = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -350, 120
    )
    roughness.set_editor_property("r", 1.0)

    specular = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -350, 200
    )
    specular.set_editor_property("r", 0.0)

    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -350, 280
    )
    opacity.set_editor_property("r", 1.0)

    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        specular, "", unreal.MaterialProperty.MP_SPECULAR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        opacity, "", unreal.MaterialProperty.MP_OPACITY
    )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(FULL_PATH, only_if_is_dirty=False)
    unreal.log(f"[create_ar_flash_receiver] saved {FULL_PATH}")


main()
