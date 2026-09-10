import argparse
import json

import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl, write_json
from werewolf_sft.validation import validate_dataset


def main():
    parser = argparse.ArgumentParser(description="Validate strict player-view JSONL")
    parser.add_argument("paths", nargs="*", default=["data/gold/dataset_v0.1/rules.jsonl"])
    parser.add_argument("--report", default="reports/validation.json")
    args = parser.parse_args()
    rows = [row for path in args.paths for row in read_jsonl(ROOT / path)]
    issues = validate_dataset(rows)
    report = {"status": "passed" if not issues else "failed", "rows": len(rows), "errors": issues}
    write_json(ROOT / args.report, report)
    print(json.dumps(report, ensure_ascii=False))
    return bool(issues)


if __name__ == "__main__":
    raise SystemExit(main())
