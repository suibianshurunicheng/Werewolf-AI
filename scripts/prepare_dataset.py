"""Build or verify immutable classic seeds, eval and stage-specific messages."""
import argparse
import json
from collections import Counter

import _bootstrap
from werewolf_sft.io import ROOT, canonical
from werewolf_sft.seed_data import rule_samples, strategy_samples, wolf_tactics
from werewolf_sft.benchmark_data import build_benchmark
from werewolf_sft.dataset import save_snapshot, jsonl_body, prepare_stage, snapshot_manifest
from werewolf_sft.validation import validate_dataset, assert_disjoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="dataset_v0.1", choices=["dataset_v0.1"])
    args = parser.parse_args()
    groups = {"rules": rule_samples(), "strategy": strategy_samples(), "tactics": wolf_tactics()}
    training = [row for rows in groups.values() for row in rows]
    issues = validate_dataset(training)
    if issues:
        raise ValueError("\n".join(issues))
    for row in training:
        row["review"]["rule_checked"] = row["review"]["perspective_checked"] = True
    suites = build_benchmark()
    evaluation = [case["scenario"] for cases in suites.values() for case in cases]
    issues = validate_dataset(evaluation)
    if issues:
        raise ValueError("\n".join(issues))
    assert_disjoint(training, evaluation)
    files = {}
    for stage, rows in groups.items():
        files[f"data/gold/{args.version}/{stage}.jsonl"] = jsonl_body(rows)
        for suffix, body in prepare_stage(rows).items():
            files[f"data/prepared/{args.version}/{stage}/{suffix}"] = body
    for suite, cases in suites.items():
        files[f"eval/{suite}.jsonl"] = jsonl_body(cases)
    manifest = snapshot_manifest(files, args.version)
    manifest.update(
        counts={key: len(value) for key, value in groups.items()},
        eval_counts={key: len(value) for key, value in suites.items()},
        source="original_synthetic", human_reviewed=False,
        notes="Small authored seed corpus, not 3000+ independent human-reviewed games.",
    )
    files[f"data/versions/{args.version}.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    save_snapshot({ROOT / path: body for path, body in files.items()})
    print(json.dumps({"status": "created_or_verified", **manifest["counts"], "evaluation": manifest["eval_counts"]}))


if __name__ == "__main__":
    main()
