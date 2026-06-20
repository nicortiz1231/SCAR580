"""Find weapon spawn/equip nodes in BP_FPCharacter EventGraph."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_weapon_spawn.log")
lines = []

bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
for g in unreal.BlueprintEditorLibrary.list_graphs(bp):
    if g.get_name() not in ("EventGraph", "BeginSetup"):
        continue
    editor = unreal.BlueprintGraphEditor.get_graph_editor(g)
    lines.append(f"=== {g.get_name()} ===")
    for node in editor.list_all_nodes():
        cls = node.get_class().get_name()
        if cls == "K2Node_SpawnActorFromClass":
            try:
                actor_class = node.get_editor_property("node_class")
                lines.append(f"SpawnActor :: {actor_class.get_name() if actor_class else None}")
            except Exception as exc:
                lines.append(f"SpawnActor ERR {exc}")
        elif cls == "K2Node_CallFunction":
            for prop in ("function_reference", "FunctionReference", "member_name", "MemberName"):
                try:
                    ref = node.get_editor_property(prop)
                    text = str(ref)
                    if any(k in text for k in ("Weapon", "Pistol", "Equip", "Spawn", "BeginSetup", "Setup", "Camera", "ViewTarget", "Possess")):
                        lines.append(f"CallFunction :: {text}")
                except Exception:
                    pass
        elif cls == "K2Node_GenericCreateObject":
            try:
                cls_obj = node.get_editor_property("class_type")
                lines.append(f"CreateObject :: {cls_obj.get_name() if cls_obj else None}")
            except Exception:
                lines.append("CreateObject :: ?")
        elif cls == "K2Node_Event":
            try:
                title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
                lines.append(f"Event :: {title}")
            except Exception:
                pass

OUT.write_text("\n".join(lines))
