import argparse
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

# Download explicitly with prepare_model.py; training and checkpoint saving
# must not probe an unpinned remote main branch or wait on network retries.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

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
        identifier = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        progress_path = folder / "progress.json"
        progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else None
        failure = {"status": "failed", "stage": args.stage, "config": config, "dry_run": args.dry_run,
                   "time_utc": identifier[:16], "last_progress": progress,
                   "error_type": type(exc).__name__, "error": str(exc).replace(str(ROOT), "<workspace>")}
        write_json(folder / "attempts" / (identifier + ".json"), failure)
        write_json(ROOT / "reports/training_attempts" / (identifier + ".json"), failure)
        write_json(folder / "attempt_failure.json", failure)
        raise


if __name__ == "__main__":
    main()
