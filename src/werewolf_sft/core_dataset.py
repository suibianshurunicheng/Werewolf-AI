"""Explicit reviewed-source assembly. Never glob candidates or admit video into v0.2."""
import json
from collections import Counter
from pathlib import Path

from .classic_messages import classic_messages, PROMPT_VERSION
from .core_supplement import supplement
from .dataset import jsonl_body, save_snapshot, snapshot_manifest, split_by_family, verify_snapshot
from .io import content_hash, read_jsonl, sha256_file
from .validation import assert_disjoint, validate_dataset

COMPONENTS = {
    "rules_batch_v0.1": "rules.jsonl",
    "strategy_batch_v0.1": "samples.jsonl",
    "core_supplement_v0.2": "samples.jsonl",
}
REQUIRED_COVERAGE = ("guard_memory", "witch_self_save", "role_boundary", "legal_plan_update",
                     "relationship_votes", "rule_correction", "evidence_update",
                     "claims_vs_facts", "wolf_private_public", "stage_boundary", "blind_autonomy")


def require_core_source(row):
    source = row["source"]
    if row["dataset_version"] != "dataset_v0.2" or row["board"] != "classic_12":
        raise ValueError("core version/board mismatch")
    if source["kind"] != "original_synthetic" or source["reference_urls"]:
        raise ValueError("v0.2 excludes video, transcript and external source data")
    if not row["id"].startswith(("v02-rule-", "v02-strategy-", "v02-core-")):
        raise ValueError("source is not an approved core component")
    if any(word in json.dumps(source, ensure_ascii=False).lower() for word in ("bilibili", "video_distilled", "transcript", "asr")):
        raise ValueError("video lineage is forbidden in v0.2")


def freeze_supplement(root):
    root = Path(root)
    rows = supplement()
    errors = validate_dataset(rows)
    if errors:
        raise ValueError("\n".join(errors))
    for row in rows:
        require_core_source(row)
    prefix = "data/candidates/dataset_v0.2/core_supplement_v0.2"
    files = {f"{prefix}/samples.jsonl": jsonl_body(rows)}
    manifest = snapshot_manifest(files, "dataset_v0.2")
    manifest.update(component="core_supplement_v0.2", rows=len(rows),
                    ready_for_training=False, source="original_synthetic",
                    supersedes="core_supplement_v0.1",
                    notes="Review corrected three sheriff-vote round fields to day one; previous candidate remains immutable and excluded. Independent core situations, not video or expert Gold.")
    files[f"{prefix}/manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    save_snapshot({root / p: text for p, text in files.items()})
    return manifest


def load_core(root):
    root = Path(root)
    old = json.loads((root / "data/versions/dataset_v0.1.json").read_text(encoding="utf-8"))
    verify_snapshot(root, old)
    rows, provenance = [], {}
    for component, filename in COMPONENTS.items():
        prefix = root / "data/candidates/dataset_v0.2" / component
        manifest = json.loads((prefix / "manifest.json").read_text(encoding="utf-8"))
        verify_snapshot(root, manifest)
        path = prefix / filename
        if path.relative_to(root).as_posix() not in manifest["files"]:
            raise ValueError("component rows not covered by manifest")
        for row in read_jsonl(path):
            require_core_source(row)
            rows.append(row)
            provenance[row["id"]] = {"path": path.relative_to(root).as_posix(),
                                     "row_sha256": content_hash(row)}
    issues = validate_dataset(rows)
    if issues:
        raise ValueError("\n".join(issues))
    evaluation = [c["scenario"] for suite in ("rules", "strategy", "counterfactual", "blind")
                  for c in read_jsonl(root / f"eval/{suite}.jsonl")]
    assert_disjoint(rows, evaluation)
    return rows, provenance


def capabilities(row):
    tags = set(row["tactical_tags"])
    family = row["scenario_id"]
    if row["training_stage"] == "rules":
        tags |= {"rule_correction", "role_boundary", "stage_boundary"}
    if family.startswith("v02-rules-"):
        tags.add(family.removeprefix("v02-rules-"))
    if family.startswith("v02-strategy-"):
        tags |= {"evidence_update", "claims_vs_facts", "stage_boundary"}
        if row["role"] == "werewolf":
            tags.add("wolf_private_public")
        if family.endswith("relationship_votes"):
            tags.add("relationship_votes")
        if family.endswith("legal_plan_update"):
            tags.add("legal_plan_update")
    return sorted(tags.intersection(REQUIRED_COVERAGE))


def coverage(rows):
    train, val = split_by_family(rows)
    matrix = {key: {split: [r["id"] for r in group if key in capabilities(r)]
                    for split, group in (("train", train), ("validation", val))}
              for key in REQUIRED_COVERAGE}
    missing = [f"{k}/{s}" for k, value in matrix.items() for s, ids in value.items() if not ids]
    stages = {stage: {s: sum(r["training_stage"] == stage for r in group)
                      for s, group in (("train", train), ("validation", val))}
              for stage in ("rules", "strategy", "tactics")}
    missing += [f"{stage}/{s}" for stage, value in stages.items() for s, count in value.items() if not count]
    return {"rows": len(rows), "families": len({r["scenario_id"] for r in rows}),
            "matrix": matrix, "stage_splits": stages, "missing": missing,
            "notes": "Coverage is presence, not expertise, statistical power or sufficient scale."}


def freeze_core(root):
    root = Path(root)
    rows, provenance = load_core(root)
    review_path = root / "reports/dataset_v02_core_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    approvals = {r["id"]: r for r in review["items"]}
    if len(approvals) != len(review["items"]) or set(approvals) != set(provenance):
        raise ValueError("every candidate requires exactly one recorded review")
    for r in rows:
        a = approvals[r["id"]]
        if a["row_sha256"] != provenance[r["id"]]["row_sha256"] or a["verdict"] != "accept_core" or not a["reason"]:
            raise ValueError("unreviewed, changed or rejected candidate")
    cover = coverage(rows)
    if cover["missing"]:
        raise ValueError("coverage gaps: " + ", ".join(cover["missing"]))
    files = {}
    for stage in ("rules", "strategy", "tactics"):
        stage_rows = [r for r in rows if r["training_stage"] == stage]
        files[f"data/gold/dataset_v0.2/{stage}.jsonl"] = jsonl_body(stage_rows)
        for split, group in zip(("train", "validation"), split_by_family(stage_rows)):
            prefix = f"data/prepared/dataset_v0.2/{stage}/{split}"
            files[prefix + ".jsonl"] = jsonl_body(group)
            files[prefix + ".messages.jsonl"] = jsonl_body([
                {"id": r["id"], "scenario_id": r["scenario_id"], "dataset_version": "dataset_v0.2",
                 "messages": classic_messages(r)} for r in group])
    manifest = snapshot_manifest(files, "dataset_v0.2")
    manifest.update(experiment="v0.2-core", video_rows=0, source_allowlist=COMPONENTS,
                    counts=dict(Counter(r["training_stage"] for r in rows)), rows=len(rows),
                    prompt_version=PROMPT_VERSION, review_kind=review["review_kind"],
                    human_reviewed=False, review_sha256=sha256_file(review_path),
                    provenance=provenance, coverage=cover,
                    notes="Reviewed core repair experiment. Freeze is not evidence of model improvement; training requires saved tokenizer/config/dry-run and commit.")
    files["data/versions/dataset_v0.2.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    save_snapshot({root / p: text for p, text in files.items()})
    return manifest
