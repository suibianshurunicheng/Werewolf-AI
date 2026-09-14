"""Dev-only frozen skill projection diagnostic; does not alter Benchmark tooling."""
import copy
import json
from pathlib import Path

from .classic_messages import SKILLS
from .config import load_config, model_revision
from .evaluation import SCORING_VERSION, summarize
from .io import ROOT, content_hash, read_jsonl, sha256_file, write_json, write_jsonl
from .perspective import player_view, to_messages
from .runtime import (adapter_digest, append_prediction, generate, load_generator,
                      prepare_journal, run_lock)

PACKET = Path("data/diagnostics/v02_skill_projection_v0.1")
OUTPUT = Path("reports/diagnostics/v02_skill_projection_v0.1")
SPEC_SHA = "bb5db53c7bf1e871089906a823f653c5bdf417fa68cff70e41e10508253ded45"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_packet(spec, packet, cases):
    ids = [p["id"] for p in packet]
    require(len(ids) == len(set(ids)) == 23 and ids == spec["case_ids"], "frozen dev IDs differ")
    require(set(ids) == {c["id"] for c in cases}, "dev selection differs")
    by_id = {c["id"]: c for c in cases}
    for item in packet:
        case = by_id[item["id"]]
        require(item["split"] == case["split"] == "dev", "test is forbidden")
        view = player_view(case["scenario"])
        require(item["control_messages"] == to_messages(view, include_answer=False), "control input changed")
        projected = copy.deepcopy(view)
        keys = SKILLS[view["role"]] + ("last_words_allowed",)
        projected["skill_state"] = {key: view["skill_state"][key] for key in keys}
        require(item["treatment_messages"] == to_messages(projected, include_answer=False),
                "only skill_state projection may change")


def load_experiment():
    require(sha256_file(ROOT / PACKET / "experiment.json") == SPEC_SHA, "frozen experiment changed")
    spec = json.loads((ROOT / PACKET / "experiment.json").read_text(encoding="utf-8"))
    require(sha256_file(ROOT / PACKET / "inputs.jsonl") == spec["packet_sha256"], "frozen packet changed")
    evidence = json.loads((ROOT / "reports/v02_core_diagnosis.json").read_text(encoding="utf-8"))
    for path, digest in evidence["sources"].items():
        require(sha256_file(ROOT / path) == digest, "frozen source changed: " + path)
    packet = read_jsonl(ROOT / PACKET / "inputs.jsonl")
    # Filter at ingestion: only dev cases reach rendering, scoring or model input.
    cases = [case for suite in ("rules", "strategy", "counterfactual", "blind")
             for case in read_jsonl(ROOT / f"eval/{suite}.jsonl") if case["split"] == "dev"]
    validate_packet(spec, packet, cases)
    config = load_config(ROOT / "configs/qlora_classic_v02.yaml")
    original = spec["source_run"]
    protocol = original["protocol"]
    require(config["inference"] == spec["generation"] == protocol["generation"], "generation differs")
    require(config["training"]["seed"] == spec["seed"] == protocol["seed"], "seed differs")
    require(config["model"]["name"] == protocol["model"] and model_revision(config) == protocol["revision"], "Base differs")
    require(config["quantization"] == protocol["quantization"] and
            config["training"]["cpu_offload"] == protocol["cpu_offload"], "runtime config differs")
    adapter = ROOT / spec["adapter"]
    require(sha256_file(adapter / "adapter_model.safetensors") == spec["adapter_safetensors_sha256"], "weights differ")
    require(adapter_digest(adapter) == original["adapter_digest"], "adapter config/digest differs")
    current_source_run = json.loads((ROOT / "reports/runs/qlora_v02/run.json").read_text(encoding="utf-8"))
    require(current_source_run == original, "source run differs")
    controls = [json.loads((ROOT / f"reports/runs/qlora_v02/cases/{i}.json").read_text(encoding="utf-8")) for i in spec["case_ids"]]
    require(all(p["run_fingerprint"] == content_hash(original) and not p["truncated"] for p in controls), "invalid control")
    sources = {name: sha256_file(ROOT / "src/werewolf_sft" / (name + ".py"))
               for name in ("skill_diagnostic", "runtime", "modeling", "perspective", "evaluation", "rules")}
    run = {"experiment_id": spec["experiment_id"], "spec_sha256": SPEC_SHA,
           "packet_sha256": spec["packet_sha256"], "config": config,
           "adapter_digest": original["adapter_digest"], "source_run": original,
           "dev_cases_hash": content_hash(cases), "control_predictions_hash": content_hash(controls),
           "source_hashes": sources, "scoring_version": SCORING_VERSION}
    return config, spec, packet, cases, controls, run


def validate_saved(predictions, packet, run):
    inputs = {p["id"]: content_hash(p["treatment_messages"]) for p in packet}
    require(len({p["id"] for p in predictions}) == len(predictions), "duplicate predictions")
    for pred in predictions:
        require(pred["id"] in inputs, "non-dev prediction in journal")
        require(pred["run_fingerprint"] == content_hash(run), "mixed prediction fingerprints")
        require(pred["input_hash"] == inputs[pred["id"]], "prediction input differs")
        require(not pred["truncated"], "truncated prediction; preserve evidence and investigate without regenerating")


def execute(directory, config, spec, packet, cases, controls, run, score_only=False,
            loader=load_generator, generator=generate):
    directory = Path(directory)
    with run_lock(directory):
        predictions = prepare_journal(directory, run)
        validate_saved(predictions, packet, run)
        done = {p["id"] for p in predictions}
        if not score_only and len(done) < len(packet):
            write_json(directory / "progress.json", {"status": "loading_model", "completed": len(done), "total": 23})
            try:
                model, tokenizer = loader(config, ROOT / spec["adapter"])
                for item in packet:
                    if item["id"] in done:
                        continue
                    result = generator(model, tokenizer, item["treatment_messages"], config)
                    pred = {"id": item["id"], "input_hash": content_hash(item["treatment_messages"]),
                            "run_fingerprint": content_hash(run), **result}
                    append_prediction(directory, pred)
                    predictions.append(pred)
                    require(not result["truncated"], "truncation: saved evidence; stop without retry")
                    write_json(directory / "progress.json", {"status": "running", "completed": len(predictions), "total": 23})
                    print(json.dumps({"completed": len(predictions), "total": 23, "id": item["id"],
                                      "seconds": result["seconds"]}), flush=True)
            except Exception as exc:
                write_json(directory / "failure.json", {"error": str(exc), "completed": len(predictions)})
                raise
        ordered = sorted(predictions, key=lambda p: spec["case_ids"].index(p["id"]))
        report = {"run_fingerprint": content_hash(run), "scoring_version": SCORING_VERSION,
                  "control": summarize(cases, controls), "treatment": summarize(cases, ordered),
                  "semantic_review": "pending", "held_out_claim": False}
        write_json(directory / "summary.json", report)
        write_jsonl(directory / "predictions.jsonl", ordered)
        write_json(directory / "progress.json", {"status": report["treatment"]["status"], "completed": len(ordered), "total": 23})
        return report
