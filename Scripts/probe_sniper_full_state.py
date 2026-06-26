"""Full sniper state: attachments, spawn chain, AutomaticBase sight path."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_sniper_full_state.log")
lines = []


def w(s=""):
    lines.append(s)


def dump_hands_slot(char):
    for g in unreal.BlueprintEditorLibrary.list_graphs(char):
        if g.get_name() != "BeginSetup":
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in ed.list_all_nodes():
            if node.get_name() != "K2Node_GenericCreateObject_2":
                continue
            w("=== HandsSlot (GenericCreateObject_2) ===")
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
                pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
                val = unreal.BlueprintGraphPinLibrary.get_pin_value(pin)
                if val:
                    w(f"  {pname}={val}")


def dump_spawn_chain(char):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char)
    )
    w("\n=== Sniper spawn exec chain ===")
    node = None
    for n in ed.list_all_nodes():
        if n.get_name() == "K2Node_VariableSet_15":
            node = n
            break
    if not node:
        w("MISSING VariableSet_15")
        return
    cur = node
    for i in range(20):
        then = cur.find_output_pin("then")
        if not then:
            break
        links = [lp for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then) if lp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT]
        if not links:
            w(f"  END at {cur.get_name()}")
            break
        nxt = links[0].get_owning_node()
        w(f"  {cur.get_name()} -> {nxt.get_name()} | {str(nxt.get_node_title()).replace(chr(10),' ')}")
        if nxt.get_name() == cur.get_name():
            w("  LOOP!")
            break
        cur = nxt


def dump_sniper_cdo():
    sniper = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper")
    cdo = unreal.get_default_object(sniper.generated_class())
    w("\n=== Sniper CDO ===")
    for p in ("ScopeSightMesh", "OpticSightMesh", "AimDistanceFromCamera", "ScopeMat_SightDistance", "ScopeMat_GradientParam", "ChangeSightSpeed"):
        try:
            v = cdo.get_editor_property(p)
            w(f"  {p}={v.get_path_name() if hasattr(v,'get_path_name') else v}")
        except Exception as exc:
            w(f"  {p} ERR {exc}")
    pv = cdo.get_editor_property("ProceduralValues")
    if pv:
        wv = pv.get_editor_property("WeaponValues")
        loc = wv.get_editor_property("BasePoseLoc")
        w(f"  BasePoseLoc=({loc.x},{loc.y},{loc.z})")


def dump_pickup_cdo():
    pickup = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper")
    cdo = unreal.get_default_object(pickup.generated_class())
    w("\n=== Pickup sniper defaults ===")
    for prop in cdo.get_class().get_properties():
        pn = prop.get_name()
        if "item" in pn.lower() or "sight" in pn.lower() or "ammo" in pn.lower():
            try:
                w(f"  {pn}={cdo.get_editor_property(pn)}")
            except Exception:
                pass


def dump_auto_spawnatt_sight_branch():
    auto = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase")
    eg = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(auto))
    for node in eg.list_all_nodes():
        if node.get_class().get_name() != "K2Node_SwitchEnum_1" and "Sights" not in str(node.get_node_title()):
            continue
        if "ENUM_Sights" not in str(node.get_node_title()):
            continue
        w(f"\n=== AutomaticBase ENUM_Sights switch {node.get_name()} ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if not pn.startswith("NewEnumerator"):
                continue
            linked = []
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                o = lp.get_owning_node()
                linked.append(f"{o.get_name()}|{str(o.get_node_title()).replace(chr(10),' ')[:60]}")
            if linked:
                w(f"  {pn} -> {linked}")


# Compare ORIG on disk
import shutil
orig_sniper = Path("/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Content/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.uasset")
scar_sniper = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Content/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.uasset")
w(f"\n=== File sizes orig={orig_sniper.stat().st_size if orig_sniper.exists() else 0} scar={scar_sniper.stat().st_size if scar_sniper.exists() else 0} ===")

char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
dump_hands_slot(char)
dump_spawn_chain(char)
dump_sniper_cdo()
dump_auto_spawnatt_sight_branch()

OUT.write_text("\n".join(lines))
