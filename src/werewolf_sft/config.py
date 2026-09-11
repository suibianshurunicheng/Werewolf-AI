"""Validated inherited YAML with no silent typo/default fallbacks."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

from .io import ROOT


def merge_dict(base, changes):
    result = copy.deepcopy(base)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_config(path, seen=None):
    path = Path(path).resolve()
    seen = set() if seen is None else set(seen)
    if path in seen:
        raise ValueError("cyclic config inheritance")
    seen.add(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config must be a mapping")
    parent = data.pop("extends", None)
    if parent:
        data = merge_dict(load_config(path.parent / parent, seen), data)
    validate_config(data)
    return data


def validate_config(data):
    expected = {"project", "model", "data", "quantization", "lora", "training", "inference", "evaluation"}
    if set(data) != expected:
        raise ValueError("config sections differ: " + str(set(data) ^ expected))
    keys = {
        "model": {"name", "revision_manifest", "trust_remote_code"},
        "data": {"version", "root", "board", "max_length", "packing", "overlength"},
        "quantization": {"enabled", "type", "double_quant", "compute_dtype"},
        "lora": {"rank", "alpha", "dropout", "target_modules"},
        "training": {"seed", "batch_size", "gradient_accumulation_steps", "gradient_checkpointing", "epochs",
                     "learning_rate", "warmup_ratio", "weight_decay", "max_grad_norm", "optimizer", "save_steps",
                     "logging_steps", "save_total_limit", "max_steps", "output_root", "cpu_offload"},
        "inference": {"max_input_tokens", "max_new_tokens", "do_sample", "use_cache"},
        "evaluation": {"suites", "benchmark_version", "baseline_dir"},
    }
    for section, allowed in keys.items():
        if set(data[section]) != allowed:
            raise ValueError(f"unknown/missing {section} keys: {set(data[section]) ^ allowed}")
    if data["model"]["trust_remote_code"]:
        raise ValueError("V1 only supports native audited architectures")
    if data["data"]["board"] != "classic_12" or data["data"]["packing"]:
        raise ValueError("Phase 1 requires classic_12 without packing")
    if data["data"]["overlength"] not in {"reject", "filter"}:
        raise ValueError("never silently truncate a training answer")
    if data["training"]["batch_size"] != 1:
        raise ValueError("V1 uses microbatch 1; increase gradient accumulation")
    for section, names in {
        "data": ["max_length"], "lora": ["rank", "alpha"],
        "training": ["gradient_accumulation_steps", "save_steps", "logging_steps", "save_total_limit"],
        "inference": ["max_input_tokens", "max_new_tokens"],
    }.items():
        for key in names:
            value = data[section][key]
            if type(value) is not int or value <= 0:
                raise ValueError(f"{section}.{key} must be a positive integer")
    if not 1 <= data["lora"]["rank"] <= 16:
        raise ValueError("V1 rank must be between 1 and 16")
    if data["quantization"]["type"] != "nf4" or not data["quantization"]["double_quant"]:
        raise ValueError("QLoRA requires NF4 and double quantization")
    if data["quantization"]["compute_dtype"] not in {"auto", "bf16", "fp16"}:
        raise ValueError("unsupported compute dtype")
    if not 0 < data["training"]["learning_rate"] <= 0.0002:
        raise ValueError("learning rate outside conservative SFT range")
    if not 0 <= data["lora"]["dropout"] < 1:
        raise ValueError("invalid dropout")
    if not data["lora"]["target_modules"]:
        raise ValueError("empty LoRA targets")
    if set(data["evaluation"]["suites"]) != {"rules", "strategy", "counterfactual", "blind"} or len(data["evaluation"]["suites"]) != 4:
        raise ValueError("V1 requires all four benchmark suites exactly once")
    if data["training"]["epochs"] <= 0 or (data["training"]["max_steps"] != -1 and data["training"]["max_steps"] <= 0):
        raise ValueError("training must have a positive duration")
    for value in [data["data"]["root"], data["training"]["output_root"], data["evaluation"]["baseline_dir"]]:
        (ROOT / value).resolve().relative_to(ROOT.resolve())


def model_revision(config):
    manifest = json.loads((ROOT / config["model"]["revision_manifest"]).read_text(encoding="utf-8"))
    if manifest["model"] != config["model"]["name"]:
        raise ValueError("model revision manifest belongs to another model")
    revision = manifest["revision"]
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("model revision must be a pinned commit")
    return revision
