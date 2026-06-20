"""Find MappingContext references and AddMappingContext usage in BP_FPCharacter."""

import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_mapping_context.log")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(msg + "\n")
    unreal.log(f"[probe_mapping_context] {msg}")


def main() -> None:
    open(LOG, "w").close()
    bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")

    for prop_name in unreal.BlueprintEditorLibrary.get_blueprint_property_names(bp):
        lower = prop_name.lower()
        if "mapping" in lower or "imc" in lower or "input" in lower:
            try:
                val = unreal.BlueprintEditorLibrary.get_blueprint_property_value(bp, prop_name)
                if val is not None:
                    if hasattr(val, "get_path_name"):
                        log(f"BP prop {prop_name} = {val.get_path_name()}")
                    else:
                        log(f"BP prop {prop_name} = {val}")
            except Exception as exc:
                log(f"BP prop {prop_name}: {exc}")

    cdo = unreal.get_default_object(bp.generated_class())
    for name in (
        "MappingContext",
        "DefaultMappingContext",
        "InputMappingContext",
        "IMC_Player",
        "MouseSens",
    ):
        try:
            val = cdo.get_editor_property(name)
            if val is not None:
                if hasattr(val, "get_path_name"):
                    log(f"CDO.{name} = {val.get_path_name()}")
                else:
                    log(f"CDO.{name} = {val}")
        except Exception:
            pass

    for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
        gname = graph.get_name()
        if gname not in ("EventGraph", "SetupPlayerInputComponent", "BeginSetup"):
            continue
        log(f"graph={gname}")
        try:
            editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            nodes = editor.get_all_nodes()
            log(f"  nodes={len(nodes)}")
            for node in nodes:
                title = str(node.get_node_title())
                if any(k in title for k in ("Mapping", "IMC", "Look", "Mouse", "Input")):
                    log(f"    {node.get_class().get_name()}: {title}")
        except Exception as exc:
            log(f"  graph err: {exc}")

    log("done")


if __name__ == "__main__":
    main()
