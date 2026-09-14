"""Print only completed, not-yet-reviewed dev pairs from the frozen diagnostic."""
import argparse
import json
import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl
from werewolf_sft.evaluation import score_case
from werewolf_sft.skill_diagnostic import OUTPUT, PACKET

parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=3)
args = parser.parse_args()
review_path = ROOT / OUTPUT / "semantic_review.json"
reviewed = {x["id"] for x in json.loads(review_path.read_text(encoding="utf-8"))["items"]} if review_path.exists() else set()
spec = json.loads((ROOT / PACKET / "experiment.json").read_text(encoding="utf-8"))
cases = {c["id"]: c for suite in ("rules", "strategy", "counterfactual", "blind")
         for c in read_jsonl(ROOT / f"eval/{suite}.jsonl") if c["split"] == "dev"}
count = 0
for identifier in spec["case_ids"]:
    path = ROOT / OUTPUT / "cases" / (identifier + ".json")
    if identifier in reviewed or not path.exists():
        continue
    case = cases[identifier]
    row = case["scenario"]
    print("CASE", identifier, "ROLE", row["role"], "STAGE", row["stage"])
    print(json.dumps({k: row[k] for k in ("seat", "round", "task", "private_info", "public_info", "skill_state")}, ensure_ascii=False))
    for name, source in (("control", ROOT / "reports/runs/qlora_v02/cases" / (identifier + ".json")), ("treatment", path)):
        pred = json.loads(source.read_text(encoding="utf-8"))
        print(name, json.dumps(score_case(case, pred["raw_response"], pred["truncated"]), ensure_ascii=False))
        print(pred["raw_response"])
    count += 1
    if count >= args.limit:
        break
