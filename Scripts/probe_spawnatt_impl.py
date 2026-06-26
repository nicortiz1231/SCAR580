"""Dump SpawnAttachments event implementation on BP_Item_Base."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_spawnatt_impl.log")
lines = []

item = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base")
for g in unreal.BlueprintEditorLibrary.list_graphs(item):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_CustomEvent_3":
            continue
        lines.append(f"=== SpawnAttachments in [{g.get_name()}] ===")
        then = node.find_then_pin()
        stack = [(then, 0)]
        while stack:
            pin, depth = stack.pop()
            if not pin or depth > 30:
                continue
            for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(pin):
                owner = lp.get_owning_node()
                title = str(owner.get_node_title()).replace("\n", " | ")
                lines.append(f"{'  '*depth}{owner.get_name()} | {title}")
                if hasattr(owner, "find_then_pin"):
                    stack.append((owner.find_then_pin(), depth + 1))
                if owner.get_class().get_name() == "K2Node_SwitchEnum":
                    for p in unreal.BlueprintEditorLibrary.list_all_pins(owner):
                        pn = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                        if pn.startswith("NewEnumerator") or pn.startswith("NUM_"):
                            for lp2 in unreal.BlueprintGraphPinLibrary.list_connected_pins(p):
                                o2 = lp2.get_owning_node()
                                lines.append(
                                    f"{'  '*(depth+1)}[{pn}] -> {o2.get_name()} | "
                                    f"{str(o2.get_node_title()).replace(chr(10),' | ')}"
                                )

# Full ENUM_Sights from generated class on pickup
pickup = unreal.load_asset(
    "/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Pickup_Sniper.BP_Weapon_Pickup_Sniper"
)
sight = unreal.get_default_object(pickup.generated_class()).get_editor_property("Item Data AttachmentsSight")
lines.append("=== all NUM_Sights ===")
for name in sorted(dir(type(sight))):
    if name.startswith("_"):
        continue
    try:
        v = getattr(type(sight), name)
        if isinstance(v, type(sight)):
            lines.append(f"  {name}={int(v)}")
    except Exception:
        pass

OUT.write_text("\n".join(lines))
