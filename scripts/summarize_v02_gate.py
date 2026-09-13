"""Summarize completed frozen-protocol runs and the predeclared video-version gate."""
import json
import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.evaluation import comparison
from werewolf_sft.io import ROOT, sha256_file, write_json
from werewolf_sft.runtime import load_cases

names = ("base_primary", "qlora_v01", "qlora_v02")
reports = {name: json.loads((ROOT / f"reports/runs/{name}/summary.json").read_text(encoding="utf-8"))
           for name in names}
comparison(reports["base_primary"], reports["qlora_v02"])
comparison(reports["qlora_v01"], reports["qlora_v02"])
review = json.loads((ROOT / "reports/dev_semantic_review_v02.json").read_text(encoding="utf-8"))
expected = {c["id"] for c in load_cases(load_config(ROOT / "configs/qlora_classic_v02.yaml"), "dev")}
if review["status"] != "complete" or {r["id"] for r in review["items"]} != expected or len(review["items"]) != len(expected):
    raise ValueError("all 23 dev cases must have a recorded semantic review")
for row in review["items"]:
    for run in ("qlora_v01", "qlora_v02"):
        if row["sources"][run] != sha256_file(ROOT / f"reports/runs/{run}/cases/{row['id']}.json"):
            raise ValueError("review source changed")
keys = ("format_valid", "action_legal", "action_match")
counts = {name: {key: round(sum(m["total"] * m[key + "_rate"] for m in report["summary"]["metrics"].values()))
                 for key in keys} for name, report in reports.items()}
for name in names:
    counts[name]["counterfactual_both_correct"] = reports[name]["summary"]["counterfactual"]["both_correct"]
deltas = {k: counts["qlora_v02"][k] - counts["qlora_v01"][k] for k in counts["qlora_v01"]}
reasons = [k + " declined by at least two cases" for k in keys if deltas[k] <= -2]
if deltas["counterfactual_both_correct"] < 0:
    reasons.append("counterfactual pair decline")
reasons += [r["id"] for r in review["items"] if r["new_critical_regression"]]
result = {"status": "complete", "protocol_fingerprint": reports["qlora_v02"]["protocol_fingerprint"],
          "counts_out_of_36": counts, "v02_minus_v01": deltas,
          "obvious_regression_gate_triggered": bool(reasons), "gate_reasons": reasons,
          "v03_may_be_considered": not reasons, "v03_created": False, "video_rows_in_v02": 0,
          "review_kind": review["review_kind"],
          "evidence_sha256": {name: sha256_file(ROOT / f"reports/runs/{name}/summary.json") for name in names},
          "review_sha256": sha256_file(ROOT / "reports/dev_semantic_review_v02.json"),
          "limitations": ["Single small deterministic benchmark; no statistical significance claim.",
                         "No independent human gameplay acceptance.",
                         "Training had six scheduled steps, three nonzero-learning-rate updates; tactics validation had one example.",
                         "Passing the no-obvious-regression gate does not establish expert quality or that every targeted defect was repaired."]}
write_json(ROOT / "reports/v02_acceptance_gate.json", result)
print(json.dumps(result, ensure_ascii=False, indent=2))
