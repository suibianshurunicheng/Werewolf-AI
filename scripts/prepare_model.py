"""Pin public upstream revision; resumable Hugging Face downloads stay in cache/."""
import argparse
import json
import os
from pathlib import Path

import _bootstrap
from werewolf_sft.io import ROOT, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Instruct-2507")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--tokenizer-only", action="store_true")
    args = parser.parse_args()
    os.environ.setdefault("HF_HOME", str(ROOT / "cache/huggingface"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
    from huggingface_hub import HfApi, snapshot_download
    name = args.model.split("/")[-1]
    manifest_path = ROOT / f"reports/models/{name}.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["model"] != args.model:
            raise ValueError("model manifest collision")
    else:
        info = HfApi().model_info(args.model)
        manifest = {"model": args.model, "revision": info.sha, "weights_downloaded": False,
                    "license": (info.card_data or {}).get("license"), "source": f"https://huggingface.co/{args.model}"}
        write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False), flush=True)
    if not args.metadata_only:
        snapshot_download(args.model, revision=manifest["revision"],
                          cache_dir=ROOT / "cache/huggingface/hub", max_workers=1,
                          allow_patterns=["*.json", "*.txt", "*.jinja", "LICENSE", "NOTICE"] +
                          ([] if args.tokenizer_only else ["*.safetensors"]))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not args.tokenizer_only:
            manifest["weights_downloaded"] = True
        write_json(manifest_path, manifest)
        print("pinned tokenizer ready" if args.tokenizer_only else "pinned model snapshot ready", flush=True)


if __name__ == "__main__":
    main()
