"""Read-only checkpoint and admission checks for the isolated video review pool."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_hash(root, path, expected):
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path outside repository: {path}")
    if hashlib.sha256(resolved.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Checkpoint content changed: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-local-frames", action="store_true")
    args = parser.parse_args()
    pool = Path(__file__).resolve().parent
    root = pool.parents[2]
    checkpoint = read(pool / "checkpoint.json")
    for path, digest in checkpoint["files_sha256"].items():
        check_hash(root, path, digest)
    evidence = read(pool / "evidence_manifest.json")
    for path, digest in evidence["source_sha256"].items():
        check_hash(root, path, digest)
    if args.with_local_frames:
        for item in evidence["frames_reinspected"]:
            check_hash(root, item["path"], item["sha256"])
    index = read(pool / "index.json")
    if index["dataset_v02_admission"] is not False:
        raise ValueError("Video pool must remain excluded from dataset_v0.2")
    counts = Counter(item["category"] for item in index["clips"])
    for category in ("CLASSIC_GOLD", "TRANSFERABLE", "BOARD_SPECIFIC", "LOW_QUALITY"):
        if counts[category] != index["counts"][category]:
            raise ValueError(f"Category count mismatch: {category}")
    ids = [item["id"] for item in index["clips"]]
    if len(ids) != len(set(ids)) or len(ids) != 4:
        raise ValueError("Legacy clip identity or deduplication changed")
    for item in index["clips"]:
        if item["admitted_to_sft"] or item["admitted_to_gold"] or item["critic_status"] != "PENDING":
            raise ValueError("This checkpoint contains no accepted training samples")
    if any(pool.rglob("*.jsonl")) or any(pool.rglob("*messages*")):
        raise ValueError("Review-only checkpoint cannot contain training exports")
    print(json.dumps({"status": "PASS", "source_documents": len(evidence["source_sha256"]),
                      "local_frames_verified": len(evidence["frames_reinspected"]) if args.with_local_frames else 0,
                      "legacy_clips": len(ids), "training_samples": 0, "critic_passed": 0,
                      "dataset_v02_admission": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
