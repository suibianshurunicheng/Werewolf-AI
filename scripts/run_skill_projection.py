"""Resume the frozen 23-dev skill projection experiment; no output override."""
import argparse
import json
import _bootstrap
from werewolf_sft.io import ROOT
from werewolf_sft.skill_diagnostic import OUTPUT, execute, load_experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()
    config, spec, packet, cases, controls, run = load_experiment()
    if args.check_only:
        print(json.dumps({"status": "validated", "dev_count": len(cases), "run": run}, ensure_ascii=False))
    else:
        print(json.dumps(execute(ROOT / OUTPUT, config, spec, packet, cases, controls, run,
                                 score_only=args.score_only), ensure_ascii=False))
