"""Read only newly completed dev answers; never print held-out test text."""
import json
import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl
from werewolf_sft.evaluation import score_case

review_path = ROOT / "reports/dev_semantic_review_v02.json"
reviewed = {r["id"] for r in json.loads(review_path.read_text(encoding="utf-8"))["items"]} if review_path.exists() else set()
cases = {c["id"]: c for suite in ("rules", "strategy", "counterfactual", "blind")
         for c in read_jsonl(ROOT / f"eval/{suite}.jsonl") if c["split"] == "dev"}
print((ROOT / "reports/runs/qlora_v02/progress.json").read_text(encoding="utf-8"))
for identifier, case in cases.items():
    path = ROOT / f"reports/runs/qlora_v02/cases/{identifier}.json"
    if identifier in reviewed or not path.exists():
        continue
    print("CASE", identifier, "ROLE", case["scenario"]["role"], "STAGE", case["scenario"]["stage"])
    for run in ("qlora_v01", "qlora_v02"):
        pred = json.loads((ROOT / f"reports/runs/{run}/cases/{identifier}.json").read_text(encoding="utf-8"))
        print(run, json.dumps(score_case(case, pred["raw_response"], pred.get("truncated", False)), ensure_ascii=False))
        try:
            fence = chr(96) * 3
            raw = pred["raw_response"].strip().removeprefix(fence + "json").removesuffix(fence).strip()
            payload = json.loads(raw)
            print(json.dumps({k: payload.get(k) for k in ("analysis", "round_assessment", "strategy", "action", "public_response")}, ensure_ascii=False))
        except (ValueError, TypeError):
            print(pred["raw_response"])
