"""Try retargeting BeginSetup HandsSlot construct object to sniper."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_retarget_sniper.log")
lines = []


def log(msg: str) -> None:
    lines.append(msg)
    unreal.log(msg)


EMPTY_HANDS_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_EmptyHands.BP_Weapon_EmptyHands"
SNIPER_PATH = "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper"

empty_bp = unreal.load_asset(EMPTY_HANDS_PATH)
sniper_bp = unreal.load_asset(SNIPER_PATH)
if not empty_bp or not sniper_bp:
    raise RuntimeError("Missing weapon blueprint assets")

old_class = empty_bp.generated_class()
new_class = sniper_bp.generated_class()
log(f"old_class={old_class.get_path_name()}")
log(f"new_class={new_class.get_path_name()}")

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
begin = None
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() == "BeginSetup":
        begin = g
        break
editor = unreal.BlueprintGraphEditor.get_graph_editor(begin)
node = None
for n in editor.list_all_nodes():
    if n.get_name() == "K2Node_GenericCreateObject_2":
        node = n
        break
if not node:
    raise RuntimeError("Missing K2Node_GenericCreateObject_2")

class_pin = node.find_input_pin("Class")
if class_pin:
    try:
        log(f"Class pin value before={unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)!r}")
    except Exception as exc:
        log(f"get_pin_value before ERR {exc}")

ok = editor.retarget_node_class(node, old_class, new_class)
log(f"retarget_node_class returned {ok}")

if class_pin:
    try:
        log(f"Class pin value after retarget={unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)!r}")
    except Exception as exc:
        log(f"get_pin_value after ERR {exc}")

for path in (
    SNIPER_PATH,
    new_class.get_path_name(),
    f"{SNIPER_PATH.rsplit('.', 1)[0]}_C",
):
    if not ok and class_pin:
        try:
            class_pin.set_pin_value(path)
            log(
                f"set_pin_value({path!r}) -> "
                f"{unreal.BlueprintGraphPinLibrary.get_pin_value(class_pin)!r}"
            )
        except Exception as exc:
            log(f"set_pin_value({path!r}) ERR {exc}")

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
OUT.write_text("\n".join(lines))
