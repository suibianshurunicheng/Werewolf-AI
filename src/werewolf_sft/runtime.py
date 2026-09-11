"""Pinned generation and fingerprinted, resumable per-case journals."""
import json
import copy
from contextlib import contextmanager
import os
import time
from pathlib import Path

from .config import model_revision
from .io import ROOT, canonical, content_hash, read_jsonl, sha256_file, write_json
from .modeling import load_base, load_tokenizer
from .perspective import SYSTEM_PROMPT, to_messages


@contextmanager
def run_lock(directory):
    """OS releases this lock on process exit, including crashes; no stale PID."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".run.lock").open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("this run is already active; do not start it twice") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_cases(config, split="all"):
    cases = []
    for suite in config["evaluation"]["suites"]:
        cases += read_jsonl(ROOT / f"eval/{suite}.jsonl")
    if any(c["benchmark_version"] != config["evaluation"]["benchmark_version"] for c in cases):
        raise ValueError("benchmark version mismatch")
    return [c for c in cases if split == "all" or c["split"] == split]


def protocol(config, cases):
    return {"model": config["model"]["name"], "revision": model_revision(config),
            "cases_hash": content_hash(cases), "system_prompt_hash": content_hash(SYSTEM_PROMPT),
            "rendered_inputs_hash": content_hash([to_messages(c["scenario"], include_answer=False) for c in cases]),
            "generation": copy.deepcopy(config["inference"]), "quantization": copy.deepcopy(config["quantization"]),
            "cpu_offload": config["training"]["cpu_offload"], "seed": config["training"]["seed"]}


def adapter_digest(path):
    if not path:
        return None
    path = Path(path)
    files = sorted(path.glob("adapter*"))
    if not files or not (path / "adapter_config.json").exists():
        raise ValueError("adapter not found")
    return content_hash({f.name: sha256_file(f) for f in files if f.is_file()})


def prepare_journal(directory, run):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "run.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != run:
            raise ValueError("run fingerprint mismatch; choose another output directory")
    else:
        write_json(path, run)
    # Individual atomic JSON files are authoritative; JSONL is an export.
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((directory / "cases").glob("*.json"))]


def append_prediction(directory, prediction):
    folder = Path(directory) / "cases"
    folder.mkdir(parents=True, exist_ok=True)
    identifier = prediction["id"]
    if not identifier or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in identifier):
        raise ValueError("unsafe case id")
    path = folder / (identifier + ".json")
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8")) != prediction:
            raise ValueError("refuse changing existing prediction")
        return
    temporary = path.with_suffix(".pending")
    temporary.write_text(canonical(prediction) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def load_generator(config, adapter=None):
    model, _ = load_base(config)
    tokenizer = load_tokenizer(config)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False)
    model.eval()
    return model, tokenizer


def generate(model, tokenizer, messages, config):
    import torch
    from transformers import set_seed
    set_seed(config["training"]["seed"])
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                             enable_thinking=False, return_tensors="pt")
    count = encoded.shape[1]
    if count > config["inference"]["max_input_tokens"]:
        raise ValueError(f"input has {count} tokens; explicit summarization required")
    encoded = encoded.to(model.get_input_embeddings().weight.device)
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    with torch.inference_mode():
        output = model.generate(input_ids=encoded, attention_mask=torch.ones_like(encoded),
            max_new_tokens=config["inference"]["max_new_tokens"],
            do_sample=config["inference"]["do_sample"], use_cache=config["inference"]["use_cache"],
            pad_token_id=tokenizer.pad_token_id)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    ids = output[0, count:].tolist()
    eos = model.generation_config.eos_token_id
    eos = eos if isinstance(eos, list) else [eos]
    return {
        "raw_response": tokenizer.decode(ids, skip_special_tokens=True),
        "input_tokens": count, "output_tokens": len(ids), "seconds": elapsed,
        "output_tokens_per_second": len(ids) / elapsed if elapsed else None,
        "peak_vram_mib": torch.cuda.max_memory_allocated() / 2**20,
        "truncated": len(ids) >= config["inference"]["max_new_tokens"] and (not ids or ids[-1] not in eos),
    }
