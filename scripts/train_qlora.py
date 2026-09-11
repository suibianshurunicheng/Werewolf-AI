import argparse
import json

import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.io import ROOT, write_json
from werewolf_sft.training import run_training


def main(default_config="configs/qlora_classic.yaml", expected_quantized=True):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=default_config)
    parser.add_argument("--stage", choices=["rules", "strategy", "tactics"], default="rules")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--initial-adapter")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_config(ROOT / args.config)
    if config["quantization"]["enabled"] != expected_quantized:
        raise ValueError("use the matching QLoRA or LoRA entrypoint")
    try:
        result = run_training(config, args.stage, args.resume,
                              ROOT / args.initial_adapter if args.initial_adapter else None, args.dry_run)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    except Exception as exc:
        folder = ROOT / config["training"]["output_root"] / args.stage
        write_json(folder / "attempt_failure.json", {"status": "failed", "stage": args.stage, "config": config,
                   "error_type": type(exc).__name__, "error": str(exc).replace(str(ROOT), "<workspace>")})
        raise


if __name__ == "__main__":
    main()
