"""Create /Game/SCAR580/Materials/M_AR_FlashCookie — additive unlit cookie for AR passthrough."""
import unreal

ASSET_PATH = "/Game/SCAR580/Materials"
ASSET_NAME = "M_AR_FlashCookie"
FULL_PATH = f"{ASSET_PATH}/{ASSET_NAME}"
COOKIE_TEX = "/Game/FirstPersonHorrorKit/Demo/FPFlashlightAnims/Mesh/Textures/T_FlashlightD.T_FlashlightD"


def main() -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(FULL_PATH):
        unreal.log(f"[create_ar_flash_cookie] already exists: {FULL_PATH}")
        return

    unreal.EditorAssetLibrary.make_directory(ASSET_PATH)
    factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(ASSET_NAME, ASSET_PATH, unreal.Material, factory)
    if not material:
        raise RuntimeError("Failed to create material asset")

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    tex_expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0
    )
    tex_expr.set_editor_property("parameter_name", "Cookie")
    cookie = unreal.load_asset(COOKIE_TEX)
    if cookie:
        tex_expr.set_editor_property("texture", cookie)

    mul = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -100, 0
    )
    strength = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 200
    )
    strength.set_editor_property("r", 8.0)

    unreal.MaterialEditingLibrary.connect_material_expressions(tex_expr, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # Use texture alpha/luminance for opacity on additive path via opacity pin when supported
    unreal.MaterialEditingLibrary.connect_material_property(tex_expr, "R", unreal.MaterialProperty.MP_OPACITY)

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(FULL_PATH, only_if_is_dirty=False)
    unreal.log(f"[create_ar_flash_cookie] created {FULL_PATH}")


main()
