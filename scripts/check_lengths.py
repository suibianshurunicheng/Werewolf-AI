"""Measure every frozen training/evaluation item with the real pinned tokenizer."""
import json
import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.encoding import encode_messages
from werewolf_sft.io import ROOT, read_jsonl, write_json
from werewolf_sft.modeling import load_tokenizer
from werewolf_sft.perspective import to_messages
from werewolf_sft.runtime import load_cases


def main():
    config = load_config(ROOT / "configs/qlora_classic.yaml")
    tokenizer = load_tokenizer(config)
    report = {}
    for stage in ("rules", "strategy", "tactics"):
        rows = []
        for split in ("train", "validation"):
            for row in read_jsonl(ROOT / config["data"]["root"] / stage / (split + ".messages.jsonl")):
                encoded = encode_messages(tokenizer, row["messages"], 32768)
                rows.append({"id": row["id"], "split": split, "tokens": len(encoded["input_ids"]),
                             "assistant_tokens": sum(t != -100 for t in encoded["labels"])})
        report[stage] = {"min": min(r["tokens"] for r in rows), "max": max(r["tokens"] for r in rows), "rows": rows}
    report["benchmark_inputs"] = [{"id": case["id"], "tokens": len(tokenizer.apply_chat_template(
        to_messages(case["scenario"], include_answer=False), tokenize=True, add_generation_prompt=True))}
        for case in load_cases(config)]
    write_json(ROOT / "reports/token_lengths.json", report)
    print(json.dumps({k: {a: b for a, b in v.items() if a != "rows"} for k, v in report.items() if isinstance(v, dict)}))
    print("benchmark max:", max(r["tokens"] for r in report["benchmark_inputs"]))


if __name__ == "__main__":
    main()
