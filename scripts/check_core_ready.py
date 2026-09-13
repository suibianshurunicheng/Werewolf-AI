"""Read-only data/tokenizer/protocol checks, saving immutable pre-training evidence."""
import json
import _bootstrap
from werewolf_sft.config import load_config, model_revision
from werewolf_sft.dataset import save_snapshot, verify_snapshot
from werewolf_sft.io import ROOT, content_hash, sha256_file
from werewolf_sft.modeling import load_tokenizer
from werewolf_sft.runtime import load_cases, protocol
from werewolf_sft.training import prepare_stage_data, effective_schedule, check_baseline

config_path = ROOT / "configs/qlora_classic_v02.yaml"
config = load_config(config_path)
manifest_path = ROOT / "data/versions/dataset_v0.2.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
verify_snapshot(ROOT, manifest)
if manifest["experiment"] != "v0.2-core" or manifest["video_rows"] != 0 or manifest["coverage"]["missing"]:
    raise ValueError("core isolation/coverage gate failed")
if sha256_file(ROOT / "reports/dataset_v02_core_review.json") != manifest["review_sha256"]:
    raise ValueError("core review has changed")
check_baseline(config)
tokenizer = load_tokenizer(config)
stages = {}
for stage in ("rules", "strategy", "tactics"):
    train, val, info = prepare_stage_data(config, stage, tokenizer)
    lengths = [len(row["input_ids"]) for row in train + val]
    stages[stage] = {**info, "min_tokens": min(lengths), "max_tokens": max(lengths),
                     "validation_lengths": [len(row["input_ids"]) for row in val],
                     "effective_schedule": effective_schedule(len(train), config["training"])}
report = {"status": "ready_for_formal_training", "config": config,
          "config_sha256": sha256_file(config_path), "dataset_manifest_sha256": sha256_file(manifest_path),
          "base_revision": model_revision(config),
          "protocol_fingerprint": content_hash(protocol(config, load_cases(config))),
          "initial_adapter": None, "stages": stages, "video_rows": 0,
          "notes": "Real pinned tokenizer and baseline protocol verified; no truncation or filtering. Starting from Base. Requires Git commit before formal training. Does not establish model quality."}
save_snapshot({ROOT / "reports/v02_training_readiness.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n"})
print(json.dumps({s: {"train": r["train_rows"], "val": r["validation_rows"],
                     "min": r["min_tokens"], "max": r["max_tokens"], "schedule": r["effective_schedule"]}
                  for s, r in stages.items()}, ensure_ascii=False))
