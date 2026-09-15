"""Audit saved schedule updates and actual tensors without loading the Base."""
import argparse
import json
from pathlib import Path
import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl, sha256_file, write_json
from export_training import clean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["B_warmup0", "C_accum8", "D_epochs2"], required=True)
    parser.add_argument("--stage", choices=["rules", "strategy", "tactics"], required=True)
    args = parser.parse_args()
    relative = Path("outputs/diagnostics/schedule_v0.1") / args.arm / args.stage
    folder = ROOT / relative
    out = ROOT / "reports/diagnostics/schedule_v0.1" / args.arm / args.stage
    manifest = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "training_result.json").read_text(encoding="utf-8"))
    logs = read_jsonl(folder / "training.jsonl")
    updates = [row for row in logs if "learning_rate" in row]
    assert [row["step"] for row in updates] == list(range(1, result["global_step"] + 1))
    from safetensors.torch import load_file
    initial_folder = None if args.stage == "rules" else folder.parent / {"strategy": "rules", "tactics": "strategy"}[args.stage] / "final"
    previous = load_file(str(initial_folder / "adapter_model.safetensors")) if initial_folder else None
    checkpoints = []
    for update in updates:
        checkpoint = folder / f"checkpoint-{update['step']}"
        marker = json.loads((checkpoint / "checkpoint_complete.json").read_text(encoding="utf-8"))
        assert all(sha256_file(checkpoint / name) == digest for name, digest in marker["files"].items())
        tensors = load_file(str(checkpoint / "adapter_model.safetensors"))
        changed = sum(not tensor.equal(previous[name]) for name, tensor in tensors.items()) if previous is not None else None
        nonzero_b = sum(bool(tensor.count_nonzero()) for name, tensor in tensors.items() if "lora_B" in name)
        assert nonzero_b > 0 and (changed is None or changed > 0)
        checkpoints.append({"step": update["step"], "epoch": update["epoch"], "applied_lr": update["learning_rate"],
            "train_loss": update["loss"], "validation_losses": [row["eval_loss"] for row in logs if row["step"] == update["step"] and "eval_loss" in row],
            "path": checkpoint.relative_to(ROOT).as_posix(), "adapter_sha256": sha256_file(checkpoint / "adapter_model.safetensors"),
            "nonzero_lora_B_tensors": nonzero_b, "changed_tensors_from_previous_checkpoint_or_initial": changed,
            "fresh_rule_first_update_proof": "LoRA B was initialized at zero; now nonzero" if previous is None else None})
        previous = tensors
    best = Path(result["best_checkpoint"])
    best_step = int(best.name.split("-")[-1])
    final_sha = sha256_file(folder / "final/adapter_model.safetensors")
    assert final_sha == sha256_file(best / "adapter_model.safetensors")
    summary = {"status": "verified", "arm": args.arm, "stage": args.stage, "optimizer_steps": len(updates),
        "nonzero_lr_steps": sum(row["learning_rate"] > 0 for row in updates), "step_epoch": [result["global_step"], result["epoch"]],
        "peak_vram_mib": result["peak_vram_mib"], "train_loss": result["metrics"]["train_loss"], "validation_loss": result["validation"]["eval_loss"],
        "checkpoints": checkpoints, "best_checkpoint": clean(str(best)), "best_step": best_step,
        "best_checkpoint_nonzero_updates_this_stage": sum(row["step"] <= best_step and row["learning_rate"] > 0 for row in updates),
        "final_checkpoint": (relative / "final").as_posix(), "final_adapter_sha256": final_sha,
        "final_equals_best": True, "weights_actually_changed": True, "dataset": manifest["dataset"],
        "dataset_manifest_sha256": sha256_file(ROOT / "data/versions/dataset_v0.2.json"), "base_model": manifest["base_model"], "base_revision": manifest["revision"],
        "initial_adapter_source": initial_folder.relative_to(ROOT).as_posix() if initial_folder else "fresh LoRA on frozen Base; no prior adapter",
        "initial_adapter_sha256": sha256_file(initial_folder / "adapter_model.safetensors") if initial_folder else None,
        "initial_adapter_digest": manifest["initial_adapter_digest"], "capability_success": "not assessed by loss; requires paired dev review"}
    target = out / "schedule_audit.json"
    if target.exists():
        assert json.loads(target.read_text(encoding="utf-8")) == summary, "Refuse to overwrite differing completed audit"
    else:
        write_json(target, summary)
    print(json.dumps({k: summary[k] for k in ("stage", "optimizer_steps", "nonzero_lr_steps", "best_step", "final_adapter_sha256", "weights_actually_changed")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
