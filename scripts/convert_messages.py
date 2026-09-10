import argparse
import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl
from werewolf_sft.dataset import save_snapshot, jsonl_body
from werewolf_sft.perspective import to_messages
from werewolf_sft.validation import validate_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = read_jsonl(ROOT / args.input)
    issues = validate_dataset(rows)
    if issues:
        raise ValueError("\n".join(issues))
    converted = [{"id": r["id"], "scenario_id": r["scenario_id"], "dataset_version": r["dataset_version"],
                  "messages": to_messages(r)} for r in rows]
    save_snapshot({ROOT / args.output: jsonl_body(converted)})
    print(f"converted_or_verified={len(converted)}")


if __name__ == "__main__":
    main()
