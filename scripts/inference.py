"""Manual one-seat helper, with an explicit public-only output mode."""
import argparse
import json

import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.evaluation import parse_response, public_leakage
from werewolf_sft.io import ROOT, write_json
from werewolf_sft.perspective import SYSTEM_PROMPT, to_messages
from werewolf_sft.rules import legal_actions
from werewolf_sft.runtime import load_generator, generate
from werewolf_sft.validation import validate_row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/qlora_classic.yaml")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-json")
    group.add_argument("--prompt-file")
    parser.add_argument("--adapter")
    parser.add_argument("--output", default="outputs/inference/result.json")
    parser.add_argument("--public-only", action="store_true")
    args = parser.parse_args()
    config = load_config(ROOT / args.config)
    row = None
    if args.input_json:
        row = json.loads((ROOT / args.input_json).read_text(encoding="utf-8"))
        errors = validate_row(row)
        if errors:
            raise ValueError("\n".join(errors))
        if row["board"] != "classic_12":
            raise ValueError("Phase 1 only supports classic_12")
        messages = to_messages(row, include_answer=False)
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": (ROOT / args.prompt_file).read_text(encoding="utf-8")}]
    model, tokenizer = load_generator(config, ROOT / args.adapter if args.adapter else None)
    result = generate(model, tokenizer, messages, config)
    write_json(ROOT / args.output, result)
    payload = parse_response(result["raw_response"])
    if result["truncated"] or public_leakage(payload, row["role"] if row else "werewolf"):
        raise ValueError("incomplete output or public leakage flag; raw result saved locally")
    if row and payload["action"] not in legal_actions(row):
        raise ValueError("illegal model action; do not copy this into the game")
    if args.public_only:
        print(payload["public_response"])
    else:
        for heading, key in [("局势分析", "analysis"), ("身份判断", "identity_reads"), ("狼坑", "wolf_pit"),
                             ("神坑", "god_pit"), ("当前轮次", "round_assessment"), ("当前策略", "strategy"),
                             ("最终行动", "action"), ("正式公开发言", "public_response")]:
            value = payload[key]
            print(f"【{heading}】\n" + (value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)))


if __name__ == "__main__":
    main()
