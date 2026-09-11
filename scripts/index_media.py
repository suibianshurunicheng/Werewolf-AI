"""Read-only Bilibili cache inventory; no board or quality verdict from titles."""
import argparse
import json
from collections import Counter
from pathlib import Path

import _bootstrap
from werewolf_sft.dataset import save_snapshot, jsonl_body
from werewolf_sft.io import ROOT, sha256_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="D:/BiliDownload")
    parser.add_argument("--version", default="catalog_v0.1")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    rows = []
    for metadata in sorted(source.rglob("videoInfo.json")):
        item = json.loads(metadata.read_text(encoding="utf-8-sig"))
        media = []
        for path in sorted(metadata.parent.glob("*.m4s")):
            with path.open("rb") as handle:
                header = handle.read(17)
            # This cache actually has nine ASCII zero bytes before MP4 ftyp.
            offset = 9 if header[:9] == b"000000000" and header[13:17] == b"ftyp" else 0
            media.append({"relative_path": path.relative_to(source).as_posix(),
                          "bytes": path.stat().st_size, "mp4_header_offset": offset,
                          "stream_type": "UNPROBED"})
        rows.append({
            "video_id": str(item["cid"]), "bvid": item.get("bvid"), "part": item.get("p"),
            "title": item.get("title"), "series": item.get("groupTitle"), "publisher": item.get("uname"),
            "source_url": "https://www.bilibili.com/video/" + item.get("bvid", ""),
            "duration_seconds": item.get("duration"), "metadata_sha256": sha256_file(metadata),
            "media": media, "board_status": "BOARD_UNKNOWN", "review_status": "NOT_REVIEWED",
            "game_family": None, "game_family_note": "Different POV videos may describe the same game; verify before splitting.",
            "transcript_status": "not_available", "commentary_is_not_player_transcript": True,
        })
    if not rows or len({r["video_id"] for r in rows}) != len(rows):
        raise ValueError("empty inventory or duplicate cid")
    folder = ROOT / "data/media" / args.version
    summary = {"catalog_version": args.version, "videos": len(rows),
               "duration_hours": sum(row["duration_seconds"] or 0 for row in rows) / 3600,
               "source_bytes": sum(m["bytes"] for r in rows for m in r["media"]),
               "series": dict(Counter(r["series"] for r in rows)),
               "reviewed": 0, "pending": len(rows), "board_classification_from_titles": False}
    queue = [{"video_id": r["video_id"], "status": "pending", "next": "probe_media_and_obtain_timestamped_evidence"}
             for r in rows]
    save_snapshot({
        folder / "sources.jsonl": jsonl_body(rows),
        folder / "queue_initial.jsonl": jsonl_body(queue),
        folder / "manifest.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    })
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == "__main__":
    main()
