"""Atomically append explicit model semantic reviews; never overwrite reviewed cases."""
import argparse
import json
import sys
import _bootstrap
from werewolf_sft.io import ROOT, sha256_file, write_json

parser = argparse.ArgumentParser()
parser.add_argument("--arm", required=True, choices=["B_warmup0", "C_accum8"])
args = parser.parse_args()
directory = ROOT / "reports/diagnostics/schedule_v0.1" / args.arm / "dev"
old = json.loads((ROOT / "reports/diagnostics/v02_skill_projection_v0.1/semantic_review.json").read_text(encoding="utf-8"))
controls = {r["id"]: r for r in old["items"]}
path = directory / "semantic_review.json"
review = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
    "status": "partial", "review_kind": "model_semantic_review_not_independent_human",
    "dimension_values": "error present true; absent false; not applicable/not assessed null",
    "control_review_source": "reports/diagnostics/v02_skill_projection_v0.1/semantic_review.json",
    "control_review_sha256": sha256_file(ROOT / "reports/diagnostics/v02_skill_projection_v0.1/semantic_review.json"), "items": []}
fields = ("role_skill", "state_reading", "permission", "team_knowledge", "public_private", "night_leak")
for item in json.load(sys.stdin):
    identifier = item["id"]
    source = controls[identifier]
    control = ROOT / "reports/runs/qlora_v02/cases" / (identifier + ".json")
    treatment = directory / "cases" / (identifier + ".json")
    assert source["sources"]["control"] == sha256_file(control)
    assert len(item["treatment_errors"]) == len(fields)
    assert all(value is None or isinstance(value, bool) for value in item["treatment_errors"])
    assert item["change"] in ("improved", "mixed", "unchanged", "regressed")
    row = {"id": identifier, "change": item["change"], "observation": item["observation"],
        "errors": {key: [source["errors"][key][0], value] for key, value in zip(fields, item["treatment_errors"])},
        "sources": {"control": sha256_file(control), "treatment": sha256_file(treatment)}}
    existing = next((r for r in review["items"] if r["id"] == identifier), None)
    if existing:
        assert existing == row, "Refuse overwrite of completed review"
    else:
        review["items"].append(row)
        write_json(path, review)
print(f"Persisted {len(review['items'])}/23 explicit semantic reviews")
