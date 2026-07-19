"""Rewrite M_AR_FlashCookie for realistic flashlight (soft falloff, no eye/pupil look)."""
import unreal

ASSET_PATH = "/Game/SCAR580/Materials"
ASSET_NAME = "M_AR_FlashCookie"
FULL_PATH = f"{ASSET_PATH}/{ASSET_NAME}"
COOKIE_TEX = "/Game/FirstPersonHorrorKit/Demo/FPFlashlightAnims/Mesh/Textures/T_FlashlightD.T_FlashlightD"


def main() -> None:
    unreal.EditorAssetLibrary.make_directory(ASSET_PATH)
    if unreal.EditorAssetLibrary.does_asset_exist(FULL_PATH):
        material = unreal.load_asset(FULL_PATH)
    else:
        factory = unreal.MaterialFactoryNew()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(ASSET_NAME, ASSET_PATH, unreal.Material, factory)
    if not material:
        raise RuntimeError("Failed to create/load material")

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    tex = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0
    )
    tex.set_editor_property("parameter_name", "Cookie")
    cookie = unreal.load_asset(COOKIE_TEX)
    if cookie:
        tex.set_editor_property("texture", cookie)

    # Sub-linear response fills dark iris gaps (Power > 1 caused the eye look).
    power = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionPower, -400, -20
    )
    softness = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -700, 160
    )
    softness.set_editor_property("parameter_name", "Softness")
    softness.set_editor_property("default_value", 0.70)

    unreal.MaterialEditingLibrary.connect_material_expressions(tex, "RGB", power, "Base")
    unreal.MaterialEditingLibrary.connect_material_expressions(softness, "", power, "Exp")

    # Slight extra soft bloom of the same cookie (add low contribution) for outer spill.
    soft_str = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -400, 160
    )
    soft_str.set_editor_property("parameter_name", "Spill")
    soft_str.set_editor_property("default_value", 0.45)

    mul_spill = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -220, 140
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(tex, "RGB", mul_spill, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(soft_str, "", mul_spill, "B")

    add = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionAdd, -80, 40
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(power, "", add, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_spill, "", add, "B")

    strength = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -80, 180
    )
    strength.set_editor_property("parameter_name", "Strength")
    strength.set_editor_property("default_value", 10.0)

    mul_str = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, 100, 40
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(add, "", mul_str, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", mul_str, "B")

    tint = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, 100, 180
    )
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", unreal.LinearColor(0.97, 0.98, 1.0, 1.0))

    mul_tint = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, 280, 40
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_str, "", mul_tint, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", mul_tint, "B")

    unreal.MaterialEditingLibrary.connect_material_property(
        mul_tint, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        tex, "R", unreal.MaterialProperty.MP_OPACITY
    )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(FULL_PATH, only_if_is_dirty=False)
    unreal.log("[update_ar_flash_cookie] soft realistic Softness=0.70 Spill=0.45 Strength=10")


main()
