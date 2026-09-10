"""Strict JSONL and deterministic artifact helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{Path(path).name}:{line_no}: empty JSONL line")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{Path(path).name}:{line_no}: invalid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{Path(path).name}:{line_no}: object required")
            rows.append(value)
    if not rows:
        raise ValueError(f"{Path(path).name}: empty dataset")
    return rows


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical(r) + "\n" for r in rows), encoding="utf-8")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def content_hash(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

