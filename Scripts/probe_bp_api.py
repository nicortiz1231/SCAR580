import unreal
bp = unreal.load_asset("/Game/BodycamFPSKIT/Blueprints/BP_FPCharacter.BP_FPCharacter")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
import inspect
help_text = str([m for m in dir(ed) if "call" in m.lower() or "connect" in m.lower() or "pin" in m.lower()])
open("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bp_api.log","w").write(help_text)
