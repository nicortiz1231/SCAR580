"""Find all SetStaticMesh targeting OpticSight or ScopeSight on character + item."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_optic_setmesh_all.log")
lines = []

def scan_bp(path, label):
    bp = unreal.load_asset(path)
    if not bp:
        lines.append(f"MISSING {path}")
        return
    for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
        editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
        for node in editor.list_all_nodes():
            if "SetStaticMesh" not in str(node.get_node_title()):
                continue
            self_pin = node.find_input_pin("self")
            mesh_pin = node.find_input_pin("NewMesh")
            self_linked = ""
            mesh_linked = ""
            if self_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(self_pin):
                    self_linked = str(lp.get_owning_node().get_node_title())
            if mesh_pin:
                for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(mesh_pin):
                    mesh_linked = str(lp.get_owning_node().get_node_title())
            mesh_val = unreal.BlueprintGraphPinLibrary.get_pin_value(mesh_pin) if mesh_pin else ""
            if "Optic" in self_linked or "Scope" in mesh_linked or "Scope" in mesh_val or "4x" in mesh_val or "Sight" in mesh_linked:
                lines.append(f"[{label}/{g.get_name()}] {node.get_name()} self={self_linked} mesh={mesh_linked or mesh_val}")
                then = node.find_output_pin("then")
                exec_in = node.find_input_pin("execute")
                if exec_in:
                    linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(exec_in)]
                    lines.append(f"  exec<- {linked}")
                if then:
                    linked = [lp.get_owning_node().get_name() for lp in unreal.BlueprintGraphPinLibrary.list_connected_pins(then)]
                    lines.append(f"  then-> {linked}")

scan_bp("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter", "CHAR")
scan_bp("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Base.BP_Item_Base", "ITEM")
scan_bp("/Game/BodycamFPSKIT/Blueprints/Interactables/Sniper/BP_Weapon_Sniper.BP_Weapon_Sniper", "SNIPER")
scan_bp("/Game/BodycamFPSKIT/Blueprints/Interactables/BP_Item_Pickup.BP_Item_Pickup", "PICKUP")

# HandsSlot attachment pin values
char = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(char):
    if g.get_name() != "BeginSetup":
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for node in editor.list_all_nodes():
        if node.get_name() != "K2Node_GenericCreateObject_2":
            continue
        lines.append("\n=== HandsSlot construct pins ===")
        for pin in unreal.BlueprintEditorLibrary.list_all_pins(node):
            pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin))
            if "Attachment" in pname or "Sight" in pname:
                lines.append(f"  {pname} = {unreal.BlueprintGraphPinLibrary.get_pin_value(pin)}")

OUT.write_text("\n".join(lines))
