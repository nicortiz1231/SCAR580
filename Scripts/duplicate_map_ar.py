import unreal
from pathlib import Path

LOG = Path("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/duplicate_map_ar.log")

def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    unreal.log(msg)

if LOG.exists():
    LOG.unlink()

src = "/Game/HandheldAR/Maps/HandheldARBlankMap"
dst = "/Game/SCAR580/Maps/Map_AR"
if unreal.EditorAssetLibrary.does_asset_exist(dst):
    log("exists")
else:
    unreal.EditorAssetLibrary.make_directory("/Game/SCAR580/Maps")
    asset = unreal.EditorAssetLibrary.duplicate_asset(src, dst)
    log(f"duplicate={asset}")
    saved = unreal.EditorAssetLibrary.save_directory("/Game/SCAR580", only_if_is_dirty=False, recursive=True)
    log(f"saved={saved}")
