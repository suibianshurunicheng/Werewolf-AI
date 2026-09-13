"""Resume explicit v0.2-core preparation; review is required before full freeze."""
import argparse
import json
import _bootstrap
from werewolf_sft.core_dataset import freeze_supplement, freeze_core, load_core, coverage
from werewolf_sft.io import ROOT

p = argparse.ArgumentParser()
p.add_argument("--freeze", action="store_true")
args = p.parse_args()
freeze_supplement(ROOT)
if args.freeze:
    manifest = freeze_core(ROOT)
    print(json.dumps({"rows": manifest["rows"], "counts": manifest["counts"], "video_rows": manifest["video_rows"]}))
else:
    print(json.dumps(coverage(load_core(ROOT)[0]), ensure_ascii=False, indent=2))
