"""Finish an interrupted export only when all planned optimizer steps are saved."""
import argparse
import json
import shutil
from pathlib import Path

import _bootstrap
from werewolf_sft.io import ROOT, sha256_file, write_json
from werewolf_sft.runtime import run_lock
from werewolf_sft.training import last_complete_checkpoint


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verified_files(checkpoint, manifest):
    if read(checkpoint / "run_manifest.json") != manifest:
        raise ValueError("checkpoint manifest differs")
    files = read(checkpoint / "checkpoint_complete.json")["files"]
    required = {"adapter_model.safetensors", "adapter_config.json", "tokenizer_config.json",
                "tokenizer.json", "trainer_state.json", "optimizer.pt", "scheduler.pt"}
    if not required.issubset(files):
        raise ValueError("checkpoint missing required files")
    for name, digest in files.items():
        if Path(name).name != name or sha256_file(checkpoint / name) != digest:
            raise ValueError("checkpoint hash mismatch")
    return files


def finalize(folder):
    folder = Path(folder).resolve()
    folder.relative_to((ROOT / "outputs").resolve())
    with run_lock(folder):
        manifest = read(folder / "run_manifest.json")
        latest = last_complete_checkpoint(folder, manifest)
        if latest is None:
            raise ValueError("no complete checkpoint")
        latest = Path(latest)
        verified_files(latest, manifest)
        state = read(latest / "trainer_state.json")
        planned = manifest["effective_schedule"]["optimizer_steps"]
        if planned < 1 or state["global_step"] != planned or state["max_steps"] != planned:
            raise ValueError("training is not complete; use training --resume")
        best = Path(state["best_model_checkpoint"]).resolve()
        if best.parent != folder:
            raise ValueError("best checkpoint outside run; explicit relocation required")
        files = verified_files(best, manifest)
        best_step = read(best / "trainer_state.json")["global_step"]
        history = [row for row in state["log_history"] if "eval_loss" in row]
        evaluation = next(row for row in reversed(history) if row["step"] == best_step)
        if evaluation["eval_loss"] != state["best_metric"] or state["best_metric"] != min(r["eval_loss"] for r in history):
            raise ValueError("best checkpoint and validation evidence disagree")
        excluded = {"optimizer.pt", "scheduler.pt", "rng_state.pth", "trainer_state.json",
                    "training_args.bin"}
        final = folder / "final"
        final.mkdir(exist_ok=True)
        for name, digest in files.items():
            if name in excluded:
                continue
            target = final / name
            if target.exists():
                if sha256_file(target) != digest:
                    raise ValueError("existing final differs; refuse overwrite")
                continue
            temporary = target.with_suffix(target.suffix + ".pending")
            shutil.copyfile(best / name, temporary)
            if sha256_file(temporary) != digest:
                raise ValueError("export copy corrupted")
            temporary.replace(target)
        result_path = folder / "training_result.json"
        if result_path.exists():
            result = read(result_path)
            if result["global_step"] != planned or result["best_checkpoint"] != str(best):
                raise ValueError("existing result differs")
            return result
        provenance = {"method": "verified_completed_checkpoint_export", "optimizer_rerun": False,
            "latest_checkpoint": str(latest), "best_checkpoint": str(best),
            "source_marker_sha256": sha256_file(best / "checkpoint_complete.json"),
            "copied_files": {n: h for n, h in files.items() if n not in excluded},
            "note": "Original process stopped after complete training/evaluation checkpoint, before final export."}
        write_json(folder / "finalization.json", provenance)
        result = {"status": "trained", "stage": manifest["stage"], "global_step": planned,
            "epoch": state["epoch"], "best_checkpoint": str(best), "peak_vram_mib": None,
            "peak_vram_note": "Not persisted before interruption; do not substitute evaluation GPU memory.",
            "metrics": {}, "metrics_note": "Per-step losses remain in training.jsonl; resumed Trainer aggregate loss/runtime are not whole-run statistics.",
            "validation": {k: v for k, v in evaluation.items() if k != "step"},
            "model_benchmark": "not_run", "finalization_method": provenance["method"]}
        write_json(result_path, result)
        write_json(folder / "progress.json", result)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(finalize(ROOT / args.run_dir), ensure_ascii=True))
