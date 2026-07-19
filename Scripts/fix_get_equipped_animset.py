"""Implement GetEquippedAnimset on BP_FPCharacter to return Pistol when armed.

ABP_Manny overwrites EquippedAnimset every frame from this interface. The
interface default returns 0 / Hands-path which selects Anim_Character_FistPose.
"""
import unreal

BP_PATH = "/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter"
ENUM_PATH = "/Game/BodycamFPSKIT/Blueprints/Enums/ENUM_Animset.ENUM_Animset"
LOG = "/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/fix_get_equipped_animset.log"

lines = []


def log(msg):
    lines.append(str(msg))
    print(msg)


bp = unreal.load_asset(BP_PATH)
enum = unreal.load_asset(ENUM_PATH)
log(f"bp={bp} enum={enum}")

if enum:
    # UserDefinedEnum API
    try:
        for i in range(16):
            try:
                name = enum.get_name_string_by_index(i)
            except Exception:
                try:
                    name = str(enum.get_editor_property("display_name_map"))
                except Exception as exc:
                    name = f"err:{exc}"
                    break
            log(f"enum[{i}]={name}")
    except Exception as exc:
        log(f"enum iterate err: {exc}")
    try:
        dmap = enum.get_editor_property("display_name_map")
        log(f"display_name_map type={type(dmap)} val={dmap}")
    except Exception as exc:
        log(f"dmap err: {exc}")

# Find existing interface function graph
func_graphs = list(bp.function_graphs)
log(f"function_graphs={[g.get_name() for g in func_graphs]}")
uber = list(bp.ubergraph_pages)
log(f"ubergraph_pages={[g.get_name() for g in uber]}")

# Implemented interfaces
try:
    ifaces = bp.get_editor_property("implemented_interfaces")
    log(f"implemented_interfaces={ifaces}")
except Exception as exc:
    log(f"ifaces err: {exc}")

# Try to find GetEquippedAnimset among all graphs
all_graphs = func_graphs + uber
for g in all_graphs:
    if "Equipped" in g.get_name() or "Animset" in g.get_name():
        log(f"FOUND GRAPH {g.get_name()} nodes={len(g.nodes)}")
        for node in g.nodes:
            title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
            log(f"  {node.get_class().get_name()} | {title}")

open(LOG, "w").write("\n".join(lines) + "\n")
log(f"wrote {LOG}")
