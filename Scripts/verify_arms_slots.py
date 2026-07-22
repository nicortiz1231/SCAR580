"""Verify ABP_FP_ArmsProcedural has a single DefaultSlot and list all Slot nodes."""
from pathlib import Path
import unreal

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/verify_arms_slots.log")
ABP = "/Game/BodycamFPSKIT/Character/ABP_FP_ArmsProcedural"


def log(msg):
    prev = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    LOG.write_text(prev + msg + "\n", encoding="utf-8")
    unreal.log(msg)


def title(n):
    try:
        return str(n.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace("\n", " | ")
    except Exception:
        return n.get_class().get_name()


def main():
    if LOG.exists():
        LOG.unlink()
    bp = unreal.load_asset(ABP)
    graphs = []
    try:
        graphs = list(unreal.AnimBlueprintLibrary.get_animation_graphs(bp))
    except Exception as e:
        log(f"get_animation_graphs: {e}")
    try:
        for g in bp.function_graphs:
            if "Anim" in g.get_name():
                graphs.append(g)
    except Exception:
        pass

    slots = []
    defaults = []
    seen = set()
    for g in graphs:
        if not g or g.get_path_name() in seen:
            continue
        seen.add(g.get_path_name())
        for n in list(g.nodes):
            if "Slot" not in n.get_class().get_name():
                continue
            t = title(n)
            slots.append((n.get_name(), t))
            if "DefaultSlot" in t:
                defaults.append((n.get_name(), t))
            log(f"SLOT {n.get_name()} :: {t}")

    log(f"defaults={len(defaults)} total_slots={len(slots)}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(ABP, only_if_is_dirty=False)
    log("compiled+saved")


main()
