"""Immutable snapshots and scenario-family splits."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .io import canonical, content_hash
from .perspective import to_messages
from .validation import validate_dataset


def jsonl_body(rows):
    return "".join(canonical(row) + "\n" for row in rows)


def save_snapshot(files):
    """Check every existing file before writing any; resume missing files only."""
    normalized = {Path(path): body for path, body in files.items()}
    for path, body in normalized.items():
        if path.exists() and path.read_text(encoding="utf-8") != body:
            raise ValueError(f"immutable snapshot differs: {path.name}; create a new dataset version")
    for path, body in normalized.items():
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".pending")
        temporary.write_text(body, encoding="utf-8", newline="\n")
        temporary.replace(path)


def split_by_family(rows):
    train, validation = [], []
    for row in rows:
        bucket = int(hashlib.sha256(row["scenario_id"].encode()).hexdigest()[:8], 16) % 5
        (validation if bucket == 0 else train).append(row)
    if not train or not validation:
        raise ValueError("both train and validation need at least one scenario family")
    return train, validation


def prepare_stage(rows):
    if any(row["board"] != "classic_12" for row in rows):
        raise ValueError("Phase 1 only accepts classic_12")
    issues = validate_dataset(rows)
    if issues:
        raise ValueError("\n".join(issues))
    train, validation = split_by_family(rows)
    messages = lambda group: [
        {"id": row["id"], "scenario_id": row["scenario_id"],
         "dataset_version": row["dataset_version"], "messages": to_messages(row)}
        for row in group
    ]
    return {
        "train.jsonl": jsonl_body(train), "validation.jsonl": jsonl_body(validation),
        "train.messages.jsonl": jsonl_body(messages(train)),
        "validation.messages.jsonl": jsonl_body(messages(validation)),
    }


def snapshot_manifest(files, version):
    return {"dataset_version": version, "files": {
        str(path).replace("\\", "/"): hashlib.sha256(body.encode("utf-8")).hexdigest()
        for path, body in sorted(files.items(), key=lambda pair: str(pair[0]))
    }}
