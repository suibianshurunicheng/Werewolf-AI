"""Schedule-arm evaluation: reuse tested atomic runner with OLD control messages."""
import argparse
import copy
import json
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import _bootstrap
from werewolf_sft.io import ROOT, content_hash, sha256_file, write_json
from werewolf_sft.config import load_config
from werewolf_sft.runtime import adapter_digest
from werewolf_sft.skill_diagnostic import load_experiment, execute
from prepare_schedule_diagnostic import flatten


def load_arm(arm):
    original, old_spec, packet, cases, controls, old_run = load_experiment()
    verification = json.loads((ROOT / "reports/training_schedule_v01_verification.json").read_text(encoding="utf-8"))
    for path, digest in verification["file_sha256"].items():
        assert sha256_file(ROOT / path) == digest, path
    protocol_path = ROOT / "data/diagnostics/training_schedule_v0.1/dev_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert protocol["case_ids"] == [p["id"] for p in packet]
    assert protocol["dev_cases_hash"] == content_hash(cases)
    assert protocol["control_messages_hash"] == content_hash([p["control_messages"] for p in packet])
    config = load_config(ROOT / f"configs/diagnostics/schedule_v0.1/{arm}.yaml")
    diff = {k for k, v in flatten(config).items() if v != flatten(original)[k]}
    allowed = {"training.warmup_ratio", "training.output_root"}
    if arm == "C_accum8":
        allowed.add("training.gradient_accumulation_steps")
    assert diff == allowed
    parent = ROOT / f"reports/diagnostics/schedule_v0.1/{arm}"
    for stage in ("rules", "strategy", "tactics"):
        audit = json.loads((parent / stage / "schedule_audit.json").read_text(encoding="utf-8"))
        assert audit["status"] == "verified"
        assert sha256_file(ROOT / audit["final_checkpoint"] / "adapter_model.safetensors") == audit["final_adapter_sha256"]
    adapter = f"outputs/diagnostics/schedule_v0.1/{arm}/tactics/final"
    # The reusable runner calls this key treatment_messages. Its contents are
    # strictly the unchanged ORIGINAL control, never skill projection.
    packet = copy.deepcopy(packet)
    for item in packet:
        item["treatment_messages"] = copy.deepcopy(item["control_messages"])
    spec = {**old_spec, "experiment_id": "training_schedule_v0.1/" + arm, "adapter": adapter,
            "adapter_safetensors_sha256": sha256_file(ROOT / adapter / "adapter_model.safetensors"),
            "intervention": "training schedule only; original control messages"}
    run = {"experiment_id": spec["experiment_id"], "config": config, "dev_protocol_sha256": sha256_file(protocol_path),
        "adapter_digest": adapter_digest(ROOT / adapter), "adapter_sha256": spec["adapter_safetensors_sha256"],
        "dev_cases_hash": content_hash(cases), "control_predictions_hash": content_hash(controls),
        "input_messages_hash": content_hash([p["control_messages"] for p in packet]),
        "source_hashes": {**old_run["source_hashes"], "schedule_runner": sha256_file(__file__)},
        "source_run": old_spec["source_run"], "scoring_version": old_run["scoring_version"]}
    directory = parent / "dev"
    target = directory / "experiment.json"
    if target.exists():
        assert json.loads(target.read_text(encoding="utf-8")) == spec
    else:
        write_json(target, spec)
    return directory, config, spec, packet, cases, controls, run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=["B_warmup0", "C_accum8"])
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()
    values = load_arm(args.arm)
    if args.preflight_only:
        target = values[0] / "preflight.json"
        evidence = {"status": "passed", "case_count": 23, "original_control_messages": True, "run": values[-1]}
        if target.exists():
            assert json.loads(target.read_text(encoding="utf-8")) == evidence
        else:
            write_json(target, evidence)
        print("23-dev schedule evaluation preflight passed; no inference")
    else:
        result = execute(*values, score_only=args.score_only)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
