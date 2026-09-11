"""Publish compact evidence and weight hashes, not large checkpoints, to reports/."""
import argparse
import json
from pathlib import Path

import _bootstrap
from werewolf_sft.io import ROOT, sha256_file, write_json
from werewolf_sft.runtime import adapter_digest
from werewolf_sft.training import last_complete_checkpoint


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        return value.replace(str(ROOT) + "\\", "").replace(str(ROOT) + "/", "").replace("\\", "/")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--initial-adapter")
    args = parser.parse_args()
    folder, destination = ROOT / args.run_dir, ROOT / args.output
    folder.resolve().relative_to((ROOT / "outputs").resolve())
    destination.resolve().relative_to((ROOT / "reports").resolve())
    manifest = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "training_result.json").read_text(encoding="utf-8"))
    if result["status"] != "trained" or not last_complete_checkpoint(folder, manifest):
        raise ValueError("no complete verified training stage")
    if json.loads((folder / "final/run_manifest.json").read_text(encoding="utf-8")) != manifest:
        raise ValueError("final and run manifests differ")
    for name in ("run_manifest.json", "training_result.json", "progress.json"):
        write_json(destination / name, clean(json.loads((folder / name).read_text(encoding="utf-8"))))
    logs = [clean(json.loads(line)) for line in (folder / "training.jsonl").read_text(encoding="utf-8").splitlines()]
    (destination / "training.jsonl").write_text(
        "".join(json.dumps(log, ensure_ascii=False) + "\n" for log in logs), encoding="utf-8", newline="\n")
    from safetensors.torch import load_file
    final = load_file(str(folder / "final/adapter_model.safetensors"))
    nonzero_b = sum(bool(tensor.count_nonzero()) for name, tensor in final.items() if "lora_B" in name)
    if not nonzero_b:
        raise ValueError("no nonzero LoRA B tensors; do not report an untrained adapter as success")
    changed = None
    if args.initial_adapter:
        initial_path = ROOT / args.initial_adapter
        if adapter_digest(initial_path) != manifest["initial_adapter_digest"]:
            raise ValueError("initial adapter fingerprint mismatch")
        initial = load_file(str(initial_path / "adapter_model.safetensors"))
        changed = sum(not tensor.equal(initial[name]) for name, tensor in final.items())
        if not changed:
            raise ValueError("stage did not update the initial adapter")
    files = {path.relative_to(ROOT).as_posix(): {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
             for path in sorted(folder.rglob("*")) if path.is_file()
             and path.name not in {".run.lock", "attempt_failure.json"} and "attempts" not in path.parts}
    report = {"training_source_commit": args.source_commit, "base_revision": manifest["revision"],
              "files": files, "adapter_tensors": len(final), "nonzero_lora_B_tensors": nonzero_b,
              "changed_tensors_from_initial_adapter": changed,
              "weights_location": folder.relative_to(ROOT).as_posix(),
              "portability": "Weights stay in local outputs; copy this directory and verify hashes when moving hosts."}
    write_json(destination / "artifacts.json", report)
    text = [
        "# " + manifest["stage"] + " QLoRA 实测", "",
        f"状态：trained；epoch={result['epoch']}，step={result['global_step']}。",
        f"数据：{manifest['dataset']['version']}；训练{manifest['dataset']['train_rows']}，验证{manifest['dataset']['validation_rows']}。",
        f"PyTorch峰值分配显存：{result['peak_vram_mib']:.1f} MiB；验证Loss：{result['validation']['eval_loss']:.6f}。",
        f"最优验证Loss checkpoint：{clean(result['best_checkpoint'])}。",
        f"非零LoRA B矩阵：{nonzero_b}；相对上一阶段改变的张量数：{changed if changed is not None else '首阶段'}。",
        "", "这里只证明真实SFT与保存成功。专项能力是否提升必须看相同Benchmark和语义审核，不能用Loss代替。",
        "Adapter和optimizer等大文件留在本机outputs；迁移主机必须复制weights_location并校验artifacts.json中的SHA，Git仓库不含这些权重。",
    ]
    (destination / "report.md").write_text("\n".join(text) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"exported": args.output, "nonzero_lora_B": nonzero_b, "changed_from_initial": changed}))


if __name__ == "__main__":
    main()
