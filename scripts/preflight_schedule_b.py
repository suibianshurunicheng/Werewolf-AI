"""Persist B-only launch checks without changing frozen experimental artifacts."""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import _bootstrap
from werewolf_sft.io import ROOT, sha256_file, write_json, content_hash, read_jsonl
from werewolf_sft.config import load_config, model_revision
from werewolf_sft.training import check_baseline
from werewolf_sft.perspective import to_messages
from werewolf_sft.runtime import load_cases
from prepare_schedule_diagnostic import flatten

OUT = ROOT / "reports/diagnostics/schedule_v0.1/B_warmup0"
CONFIG = "configs/diagnostics/schedule_v0.1/B_warmup0.yaml"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "launch_preflight.json"
    if target.exists():
        saved = json.loads(target.read_text(encoding="utf-8"))
        for path, digest in saved["frozen_files"].items():
            assert sha256_file(ROOT / path) == digest, path
        print("Existing passed launch preflight retained; no overwrite.")
        return
    verification = json.loads((ROOT / "reports/training_schedule_v01_verification.json").read_text(encoding="utf-8"))
    frozen = verification["file_sha256"]
    for path, digest in frozen.items():
        assert sha256_file(ROOT / path) == digest, path
    config = load_config(ROOT / CONFIG)
    original = flatten(load_config(ROOT / "configs/qlora_classic_v02.yaml"))
    diff = {k: {"A": original[k], "B": v} for k, v in flatten(config).items() if original[k] != v}
    assert set(diff) == {"training.output_root", "training.warmup_ratio"}
    check_baseline(config)  # Existing immutable benchmark fingerprint only, no test scoring/selection.
    cases = load_cases(config, "dev")
    packet_path = ROOT / "data/diagnostics/v02_skill_projection_v0.1/inputs.jsonl"
    assert sha256_file(packet_path) == "571465162ddb6e2ad5224da972e1017b2d2fbcb14b59f1f4dd6d72f2fe0afb3d"
    packet = read_jsonl(packet_path)
    assert len(cases) == len(packet) == 23
    for case, item in zip(cases, packet):
        assert case["id"] == item["id"] and case["split"] == item["split"] == "dev"
        assert to_messages(case["scenario"], include_answer=False) == item["control_messages"]
    disks = {drive: shutil.disk_usage(drive).free / 2**30 for drive in ("C:\\", "D:\\")}
    assert disks["C:\\"] > 3, "Insufficient working disk space; follow migration instruction"
    commands = [["scripts/check_environment.py"]] + [["scripts/train_qlora.py", "--config", CONFIG, "--stage", stage, "--dry-run"] for stage in ("rules", "strategy", "tactics")]
    outputs = []
    for args in commands:
        process = subprocess.run([sys.executable, "-X", "utf8", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        evidence = {"arguments": args, "returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr.replace(str(ROOT), "<workspace>")}
        if process.returncode:
            write_json(OUT / "launch_failure.json", evidence)
            raise RuntimeError(f"Preflight command failed: {args}")
        evidence["result"] = json.loads(process.stdout)
        outputs.append(evidence)
    assert outputs[0]["result"]["nf4_forward_backward"] and outputs[0]["result"]["cuda_available"]
    for result in [row["result"] for row in outputs[1:]]:
        assert result["effective_schedule"]["optimizer_steps"] == 2
        assert result["effective_schedule"]["warmup_steps"] == 0
        assert not result["dropped_train"] and not result["dropped_validation"]
    sources = {p: sha256_file(ROOT / p) for p in ("src/werewolf_sft/training.py", "src/werewolf_sft/modeling.py", "src/werewolf_sft/encoding.py", "src/werewolf_sft/dataset.py", "src/werewolf_sft/evaluation.py", "src/werewolf_sft/runtime.py")}
    write_json(target, {"status": "passed", "utc": datetime.now(timezone.utc).isoformat(), "config_diff": diff,
        "frozen_files": frozen, "source_sha256": sources, "base_revision": model_revision(config),
        "dataset_manifest_sha256": sha256_file(ROOT / "data/versions/dataset_v0.2.json"),
        "original_dev_messages_verified": 23, "dev_cases_hash": content_hash(cases), "free_disk_gib": disks,
        "commands": outputs, "test_used_for_selection": False, "actual_B_training_started": False})
    print("B launch preflight passed: NF4 backward, three dry-runs, frozen protocol/data/config checks.")


if __name__ == "__main__":
    main()
