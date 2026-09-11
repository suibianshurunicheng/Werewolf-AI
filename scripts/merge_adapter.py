"""Merge on CPU in full precision, never merge into a 4-bit training base."""
import argparse
import json

import _bootstrap
from werewolf_sft.config import load_config, model_revision
from werewolf_sft.io import ROOT, write_json
from werewolf_sft.modeling import load_tokenizer, setup_cache


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/qlora_classic.yaml")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = load_config(ROOT / args.config)
    destination = (ROOT / args.output).resolve()
    destination.relative_to((ROOT / "outputs").resolve())
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("refuse overwriting an existing merged model")
    adapter = ROOT / args.adapter
    manifest = json.loads((adapter / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest["base_model"] != config["model"]["name"] or manifest["revision"] != model_revision(config):
        raise ValueError("adapter/Base mismatch")
    setup_cache()
    import torch
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    base = AutoModelForCausalLM.from_pretrained(config["model"]["name"], revision=model_revision(config),
        trust_remote_code=False, torch_dtype=torch.float32, device_map={"": "cpu"},
        local_files_only=True, cache_dir=ROOT / "cache/huggingface/hub")
    merged = PeftModel.from_pretrained(base, str(adapter)).merge_and_unload(safe_merge=True)
    merged.save_pretrained(destination, safe_serialization=True, max_shard_size="2GB")
    load_tokenizer(config).save_pretrained(destination)
    write_json(destination / "run_manifest.json", manifest)
    print("merged model saved under outputs; do not add weights to Git")


if __name__ == "__main__":
    main()
