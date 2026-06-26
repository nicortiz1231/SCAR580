"""Same probe but intended for pristine BODYCAMFPSKIT project."""
import unreal
from pathlib import Path

OUT = Path("/Users/nickortiz/Documents/Unreal Projects/BODYCAMFPSKIT/Scripts/probe_bodycam_fresh_compare_orig.log")
exec(open("/Users/nickortiz/Documents/Unreal Projects/SCAR-580/Scripts/probe_bodycam_fresh_compare.py").read().replace(
    "probe_bodycam_fresh_compare.log",
    "probe_bodycam_fresh_compare_orig.log",
))
