"""Freeze an offline dev-only diagnosis and one-variable input ablation packet."""
import copy
import json
from collections import Counter

import _bootstrap
from werewolf_sft.classic_messages import SKILLS, SYSTEM
from werewolf_sft.config import load_config
from werewolf_sft.dataset import jsonl_body, save_snapshot, verify_snapshot
from werewolf_sft.io import ROOT, content_hash, read_jsonl, sha256_file
from werewolf_sft.modeling import load_tokenizer
from werewolf_sft.perspective import SYSTEM_PROMPT, player_view, to_messages


def main():
    source_files = set()

    def read(relative):
        source_files.add(relative)
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    for version in ("dataset_v0.1", "dataset_v0.2"):
        verify_snapshot(ROOT, read(f"data/versions/{version}.json"))
    review = read("reports/dev_semantic_review_v02.json")
    assert review["status"] == "complete"
    config = load_config(ROOT / "configs/qlora_classic_v02.yaml")
    tokenizer = load_tokenizer(config)
    evidence = {"status": "offline_diagnosis_complete_generation_not_started",
                "test_text_used": False, "new_training": False, "video_rows": 0,
                "training": {}, "dev": []}
    for stage in ("rules", "strategy", "tactics"):
        groups = {}
        for split in ("train", "validation"):
            path = f"data/prepared/dataset_v0.2/{stage}/{split}.jsonl"
            source_files.add(path)
            rows = read_jsonl(ROOT / path)
            groups[split] = {"rows": len(rows),
                             "roles": dict(sorted(Counter(r["role"] for r in rows).items())),
                             "actions": dict(sorted(Counter(r["action"]["type"] for r in rows).items()))}
        manifest = read(f"reports/training/{stage}_v02/run_manifest.json")
        logpath = f"reports/training/{stage}_v02/training.jsonl"
        source_files.add(logpath)
        groups["schedule"] = manifest["effective_schedule"]
        groups["logged_optimizer_steps"] = [r for r in read_jsonl(ROOT / logpath) if "learning_rate" in r]
        evidence["training"][stage] = groups
    packet = []
    reviewed = {r["id"]: r for r in review["items"]}
    # Filter before scenario rendering, tokenization, or output. No test text is emitted.
    for suite in ("rules", "strategy", "counterfactual", "blind"):
        relative = f"eval/{suite}.jsonl"
        source_files.add(relative)
        for case in read_jsonl(ROOT / relative):
            if case["split"] != "dev":
                continue
            identifier = case["id"]
            assert identifier in reviewed
            row = player_view(case["scenario"])
            projected = copy.deepcopy(row)
            keep = SKILLS[row["role"]] + ("last_words_allowed",)
            projected["skill_state"] = {k: row["skill_state"][k] for k in keep}
            assert {k: v for k, v in row.items() if k != "skill_state"} == {
                k: v for k, v in projected.items() if k != "skill_state"}
            control_messages = to_messages(row, include_answer=False)
            treatment_messages = to_messages(projected, include_answer=False)
            assert control_messages[0] == treatment_messages[0]
            assert len(control_messages) == len(treatment_messages) == 2
            lengths = {name: len(tokenizer.apply_chat_template(messages, tokenize=True,
                       add_generation_prompt=True, enable_thinking=False))
                       for name, messages in (("control", control_messages), ("treatment", treatment_messages))}
            assert max(lengths.values()) <= config["inference"]["max_input_tokens"]
            prediction = f"reports/runs/qlora_v02/cases/{identifier}.json"
            source_files.add(prediction)
            assert sha256_file(ROOT / prediction) == reviewed[identifier]["sources"]["qlora_v02"]
            item = {"id": identifier, "role": row["role"], "stage": row["stage"],
                    "kept_skill_state": projected["skill_state"],
                    "removed_skill_keys": sorted(set(row["skill_state"]) - set(keep)),
                    "input_tokens": lengths, "existing_prediction_sha256": sha256_file(ROOT / prediction)}
            evidence["dev"].append(item)
            packet.append({"id": identifier, "split": "dev", "control_messages": control_messages,
                           "treatment_messages": treatment_messages})
    assert len(packet) == 23 and {p["id"] for p in packet} == set(reviewed)
    evidence["prompt_hashes"] = {"classic_training": content_hash(SYSTEM),
                                 "frozen_evaluation": content_hash(SYSTEM_PROMPT)}
    source_files.update(("src/werewolf_sft/classic_messages.py", "src/werewolf_sft/perspective.py",
                         "src/werewolf_sft/training.py", "src/werewolf_sft/encoding.py",
                         "configs/qlora_classic_v02.yaml", "scripts/diagnose_v02_core.py"))
    evidence["sources"] = {p: sha256_file(ROOT / p) for p in sorted(source_files)}
    packet_body = jsonl_body(packet)
    import hashlib
    spec = {"experiment_id": "v02_skill_projection_v0.1", "status": "prepared_not_run",
            "single_variable": "skill_state keys retained by current Classic role plus last_words_allowed",
            "control": "existing qlora_v02 dev predictions; original renderer and system prompt",
            "treatment": "same renderer and system prompt; only skill_state projection changes",
            "adapter": "outputs/classic_v02/tactics/final",
            "adapter_safetensors_sha256": "f7b0075954f1d3daa59677f994e68ea931b830a7e732585e060f07f5e787f687",
            "source_run": read("reports/runs/qlora_v02/run.json"),
            "case_ids": [p["id"] for p in packet], "case_count": 23,
            "packet_sha256": hashlib.sha256(packet_body.encode("utf-8")).hexdigest(),
            "generation": config["inference"], "seed": config["training"]["seed"],
            "outcome_policy": "Report all 23 paired dev cases with original strict scoring and semantic role/state/private-information review. No post-hoc action aliases. Improvement is diagnostic, not held-out acceptance or permission to merge video.",
            "stop_policy": "Abort on source/adapter/packet mismatch or truncation; save per-case outputs atomically and resume missing cases only.",
            "limits": "Tests combined sensitivity to irrelevant skill keys, not individual-key causality. System wording, action dictionary and user layout remain unchanged. No new dataset, test inference or training."}
    base = ROOT / "data/diagnostics/v02_skill_projection_v0.1"
    files = {ROOT / "reports/v02_core_diagnosis.json": json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
             base / "inputs.jsonl": packet_body,
             base / "experiment.json": json.dumps(spec, ensure_ascii=False, indent=2) + "\n"}
    save_snapshot(files)
    print(json.dumps({"dev_cases": len(packet), "training": evidence["training"],
          "input_token_ranges": {name: [min(d["input_tokens"][name] for d in evidence["dev"]),
                                        max(d["input_tokens"][name] for d in evidence["dev"])]
                                 for name in ("control", "treatment")},
          "status": evidence["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
