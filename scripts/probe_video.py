"""Decode one catalogued source without modifying the original Bilibili cache."""
import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path

import av
import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl, write_json


def digest(path, offset=0):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        handle.seek(offset)
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--source", default="D:/BiliDownload")
    parser.add_argument("--catalog", default="data/media/catalog_v0.1/sources.jsonl")
    parser.add_argument("--times", type=float, nargs="+", default=[0, 30, 120, 300, 600, 900])
    args = parser.parse_args()
    if not args.video_id.isdigit() or any(not math.isfinite(t) or t < 0 for t in args.times):
        raise ValueError("Numeric video id and finite nonnegative timestamps required")
    rows = read_jsonl(ROOT / args.catalog)
    row = next(r for r in rows if r["video_id"] == args.video_id)
    if any(t > row["duration_seconds"] for t in args.times):
        raise ValueError("Frame request outside video duration")
    source = Path(args.source).resolve()
    output = ROOT / "cache/media" / row["video_id"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "probe.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "video_id": row["video_id"], "bvid": row["bvid"], "streams": [], "frames": {},
        "review_status": "NOT_REVIEWED",
        "warning": "Frames may contain audience-only identities; do not put these into player inputs.",
    }
    known = {entry["source_relative_path"]: entry for entry in manifest["streams"]}
    for media in row["media"]:
        original = (source / media["relative_path"]).resolve()
        original.relative_to(source)
        if original.stat().st_size != media["bytes"]:
            raise ValueError("Source size differs from frozen catalog")
        raw_hash = digest(original)
        container_hash = digest(original, media["mp4_header_offset"])
        target = output / (original.stem + ".mp4")
        old = known.get(media["relative_path"])
        if target.exists() and digest(target) != container_hash:
            raise ValueError("Cached container differs from source bytes; refuse overwrite")
        if old and (old["source_sha256"] != raw_hash or not target.exists()
                    or digest(target) != old["decoded_container_sha256"]):
            raise ValueError("Existing probe source or cache changed; do not overwrite")
        if not target.exists():
            temporary = target.with_suffix(".pending")
            with original.open("rb") as reader, temporary.open("wb") as writer:
                reader.seek(media["mp4_header_offset"])
                shutil.copyfileobj(reader, writer)
            temporary.replace(target)
        with av.open(str(target)) as container:
            streams = [{"type": s.type, "codec": s.codec_context.name,
                        "duration_seconds": float(s.duration * s.time_base) if s.duration else None}
                       for s in container.streams]
            if not old:
                entry = {"source_relative_path": media["relative_path"], "source_sha256": raw_hash,
                         "removed_prefix_bytes": media["mp4_header_offset"],
                         "decoded_container": target.relative_to(ROOT).as_posix(),
                         "decoded_container_sha256": digest(target), "streams": streams}
                manifest["streams"].append(entry)
                write_json(manifest_path, manifest)
            if not container.streams.video:
                continue
            video = container.streams.video[0]
            for seconds in args.times:
                if seconds < 0 or seconds > row["duration_seconds"]:
                    raise ValueError("Frame request outside video duration")
                key = f"{seconds:.3f}"
                if key in manifest["frames"]:
                    saved = ROOT / manifest["frames"][key]["path"]
                    if digest(saved) != manifest["frames"][key]["sha256"]:
                        raise ValueError("Existing frame changed")
                    continue
                container.seek(int(seconds / video.time_base), stream=video, backward=True)
                for frame in container.decode(video):
                    if frame.time is not None and frame.time >= seconds:
                        path = output / f"frame_{seconds:08.3f}.jpg"
                        temporary = path.with_suffix(".pending")
                        frame.to_image().save(temporary, format="JPEG", quality=92)
                        temporary.replace(path)
                        manifest["frames"][key] = {
                            "requested_seconds": seconds, "actual_seconds": frame.time,
                            "path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}
                        write_json(manifest_path, manifest)
                        break
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == "__main__":
    main()
