"""Freeze a small conditional schedule matrix; CPU/tokenizer preflight, no training."""
import copy
import json
from pathlib import Path
import _bootstrap
from werewolf_sft.config import load_config, validate_config
from werewolf_sft.dataset import save_snapshot, verify_snapshot
from werewolf_sft.io import ROOT, content_hash, read_jsonl, sha256_file
from werewolf_sft.modeling import load_tokenizer
from werewolf_sft.training import effective_schedule, prepare_stage_data


def flatten(value, prefix=""):
    result = {}
    for key, item in value.items():
        name = prefix + key
        result.update(flatten(item, name + ".") if isinstance(item, dict) else {name: item})
    return result


def main():
    import torch
    import transformers
    import yaml
    from transformers import get_cosine_schedule_with_warmup
    baseline = load_config(ROOT / "configs/qlora_classic_v02.yaml")
    manifest = json.loads((ROOT / "data/versions/dataset_v0.2.json").read_text(encoding="utf-8"))
    verify_snapshot(ROOT, manifest)
    packet_root = ROOT / "data/diagnostics/v02_skill_projection_v0.1"
    packet = read_jsonl(packet_root / "inputs.jsonl")
    spec = json.loads((packet_root / "experiment.json").read_text(encoding="utf-8"))
    assert sha256_file(packet_root / "inputs.jsonl") == spec["packet_sha256"]
    assert len(packet) == 23 and all(p["split"] == "dev" for p in packet)
    cases = [c for suite in ("rules", "strategy", "counterfactual", "blind")
             for c in read_jsonl(ROOT / f"eval/{suite}.jsonl") if c["split"] == "dev"]
    assert [p["id"] for p in packet] == [c["id"] for c in cases]
    tokenizer = load_tokenizer(baseline)
    stages = {}
    for stage in ("rules", "strategy", "tactics"):
        train, val, info = prepare_stage_data(baseline, stage, tokenizer)
        stages[stage] = {"train_rows": len(train), "validation_rows": len(val),
                         "data_info": info, "validation_lengths": [len(x["input_ids"]) for x in val]}
    configs = {"A_current": baseline}
    for name, change in (("B_warmup0", {"warmup_ratio": 0.0}),
                         ("C_accum8", {"warmup_ratio": 0.0, "gradient_accumulation_steps": 8}),
                         ("D_epochs2", {"warmup_ratio": 0.0, "epochs": 2})):
        cfg = copy.deepcopy(baseline)
        cfg["training"].update(change, output_root="outputs/diagnostics/schedule_v0.1/" + name)
        validate_config(cfg)
        assert cfg["data"] == baseline["data"] and cfg["inference"] == baseline["inference"]
        configs[name] = cfg
    expected = {"B_warmup0": {"training.warmup_ratio", "training.output_root"},
                "C_accum8": {"training.gradient_accumulation_steps", "training.output_root"},
                "D_epochs2": {"training.epochs", "training.output_root"}}
    matrix = {}
    for name, cfg in configs.items():
        comparator = "A_current" if name in ("A_current", "B_warmup0") else "B_warmup0"
        original = flatten(configs[comparator])
        differences = {k: {"control": original[k], "variant": v} for k, v in flatten(cfg).items() if v != original[k]}
        if name != "A_current":
            assert set(differences) == expected[name]
        plans = {}
        for stage, data in stages.items():
            schedule = effective_schedule(data["train_rows"], cfg["training"])
            parameter = torch.nn.Parameter(torch.zeros(1))
            # SGD is only an LR carrier, not an equivalence test of the 8-bit optimizer.
            optimizer = torch.optim.SGD([parameter], lr=cfg["training"]["learning_rate"])
            scheduler = get_cosine_schedule_with_warmup(optimizer, schedule["warmup_steps"], schedule["optimizer_steps"])
            applied_lrs = []
            for _ in range(schedule["optimizer_steps"]):
                applied_lrs.append(optimizer.param_groups[0]["lr"])
                parameter.grad = torch.zeros_like(parameter)
                optimizer.step()
                scheduler.step()
            actual = None
            if name == "A_current":
                logs = read_jsonl(ROOT / f"reports/training/{stage}_v02/training.jsonl")
                actual_lrs = [row["learning_rate"] for row in logs if "learning_rate" in row]
                assert actual_lrs == applied_lrs
                actual = {"logged_lrs": actual_lrs, "nonzero_lr_steps": sum(lr > 0 for lr in actual_lrs)}
            plans[stage] = {**schedule, "train_rows": data["train_rows"],
                            "planned_lr_at_optimizer_step": applied_lrs,
                            "planned_nonzero_lr_steps": sum(lr > 0 for lr in applied_lrs),
                            "actual_training_evidence": actual}
        matrix[name] = {"status": "existing_reference_do_not_retrain" if name == "A_current" else "planned_not_trained",
                        "comparator": comparator, "config_changes": differences, "stages": plans,
                        "total_planned_optimizer_steps": sum(p["optimizer_steps"] for p in plans.values()),
                        "total_planned_nonzero_lr_steps": sum(p["planned_nonzero_lr_steps"] for p in plans.values())}
    # Bind the OLD control inputs, not the projection treatment, for every future arm.
    protocol = {"scope": "exact 23 existing dev only", "case_ids": spec["case_ids"],
                "dev_cases_hash": content_hash(cases),
                "messages_source": "data/diagnostics/v02_skill_projection_v0.1/inputs.jsonl:control_messages",
                "control_messages_hash": content_hash([p["control_messages"] for p in packet]),
                "parent_protocol": spec["source_run"]["protocol"], "scoring_version": "strict-actions-v1.1",
                "original_control_predictions": "reports/runs/qlora_v02/cases",
                "test_inference": False, "video_data": False}
    report = {"experiment_id": "training_schedule_v0.1", "status": "matrix_preflight_complete_no_new_training",
              "date": "2026-09-15", "matrix": matrix, "encoded_data": stages,
              "config_sha256": {k: content_hash(v) for k, v in configs.items()},
              "dataset_manifest_sha256": sha256_file(ROOT / "data/versions/dataset_v0.2.json"),
              "dev_protocol_fingerprint": content_hash(protocol),
              "cpu_scheduler_scope": "LR-at-step verification using installed cosine scheduler; no Base loaded, no 4B training, not paged_adamw_8bit equivalence",
              "transformers_version": transformers.__version__,
              "trainer_source_sha256": sha256_file(Path(transformers.__file__).parent / "trainer.py"),
              "project_training_source_sha256": sha256_file(ROOT / "src/werewolf_sft/training.py"),
              "execution_order": ["A reuse", "B first", "C conditional after B dev review", "D conditional after B/C review"],
              "unverified": ["schedule as primary cause", "more epochs benefit", "stage forgetting", "held-out improvement"]}
    folder = ROOT / "data/diagnostics/training_schedule_v0.1"
    files = {folder / "A_current.config.json": json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
             folder / "dev_protocol.json": json.dumps(protocol, ensure_ascii=False, indent=2) + "\n",
             ROOT / "reports/training_schedule_v01_preflight.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n"}
    for name in ("B_warmup0", "C_accum8", "D_epochs2"):
        files[ROOT / f"configs/diagnostics/schedule_v0.1/{name}.yaml"] = yaml.safe_dump(configs[name], allow_unicode=True, sort_keys=False)
    save_snapshot(files)
    print(json.dumps({"status": report["status"], "matrix": {k: {"steps": v["total_planned_optimizer_steps"], "nonzero_lr_steps": v["total_planned_nonzero_lr_steps"]} for k, v in matrix.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
