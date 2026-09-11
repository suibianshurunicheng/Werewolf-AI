"""Snapshot finished immutable cases while generation continues; never mark a run complete."""
import argparse
import json

import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.evaluation import summarize, SCORING_VERSION
from werewolf_sft.io import ROOT, content_hash, write_json
from werewolf_sft.reporting import write_evaluation_report
from werewolf_sft.runtime import load_cases, protocol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/qlora_classic.yaml")
    parser.add_argument("--run", default="reports/runs/base_primary")
    parser.add_argument("--output", default="reports/base_progress")
    args = parser.parse_args()
    config = load_config(ROOT / args.config)
    cases = load_cases(config)
    directory = ROOT / args.run
    run = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    if run["protocol_fingerprint"] != content_hash(protocol(config, cases)):
        raise ValueError("config and recorded evaluation protocol differ")
    predictions = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((directory / "cases").glob("*.json"))]
    if any(p["run_fingerprint"] != content_hash(run) for p in predictions):
        raise ValueError("mixed prediction fingerprints")
    report = {**run, "scoring_version": SCORING_VERSION, "summary": summarize(cases, predictions), "snapshot_only": True,
              "completed_case_ids": sorted(p["id"] for p in predictions)}
    output = ROOT / args.output
    write_json(output.with_suffix(".json"), report)
    write_evaluation_report(output.with_suffix(".md"), report, cases, predictions)
    print(json.dumps({"snapshot": True, "completed": len(predictions), "total": len(cases)}))


if __name__ == "__main__":
    main()
