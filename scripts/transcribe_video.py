"""Pinned CPU ASR, atomic chunks, strict resume, local audio only."""
import argparse
import json
import math
import os
from pathlib import Path

import _bootstrap
from werewolf_sft.io import ROOT, content_hash, write_json
from werewolf_sft.runtime import run_lock
from probe_video import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--config", default="configs/media_asr_v01.json")
    parser.add_argument("--download-model", action="store_true")
    parser.add_argument("--max-chunks", type=int, help="Bound this invocation; existing chunks are skipped")
    args = parser.parse_args()
    if not args.video_id.isdigit() or (args.max_chunks is not None and args.max_chunks < 1):
        raise ValueError("numeric video id and positive max-chunks required")
    config = json.loads((ROOT / args.config).read_text(encoding="utf-8"))
    if config["device"] != "cpu" or config["chunk_seconds"] <= 0:
        raise ValueError("CPU processing and positive chunks required")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    from huggingface_hub import snapshot_download
    model_path = Path(snapshot_download(
        config["model"], revision=config["revision"],
        cache_dir=str(ROOT / "cache/media_models"), local_files_only=not args.download_model,
        allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]))
    model_files = {n: digest(model_path / n)
                   for n in ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]}
    write_json(ROOT / "reports/media/asr_model.json", {
        "model": config["model"], "revision": config["revision"], "files": model_files})
    if args.download_model:
        print(json.dumps({"model_ready": True, "revision": config["revision"]}))
        return
    folder = ROOT / "cache/media" / args.video_id
    probe = json.loads((folder / "probe.json").read_text(encoding="utf-8"))
    streams = [s for s in probe["streams"] if any(c["type"] == "audio" for c in s["streams"])]
    if len(streams) != 1:
        raise ValueError("exactly one probed audio stream required")
    source = streams[0]
    audio_path = ROOT / source["decoded_container"]
    if digest(audio_path) != source["decoded_container_sha256"]:
        raise ValueError("audio cache differs from probed source")
    from importlib.metadata import version
    manifest = {"config": config, "video_id": args.video_id, "audio_sha256": digest(audio_path),
                "model_files": model_files, "script_sha256": digest(Path(__file__)),
                "dependencies": {p: version(p) for p in ["faster-whisper", "ctranslate2", "av", "numpy"]}}
    fingerprint = content_hash(manifest)
    output = folder / config["version"]
    with run_lock(output):
        saved = output / "run.json"
        if saved.exists() and json.loads(saved.read_text(encoding="utf-8")) != manifest:
            raise ValueError("ASR protocol changed; use a new version, do not overwrite")
        if not saved.exists():
            write_json(saved, manifest)
        from faster_whisper import WhisperModel
        from faster_whisper.audio import decode_audio
        audio = decode_audio(str(audio_path), sampling_rate=16000)
        duration = len(audio) / 16000
        total = math.ceil(duration / config["chunk_seconds"])
        done = {}
        for p in sorted((output / "chunks").glob("*.json")):
            row = json.loads(p.read_text(encoding="utf-8"))
            stored_hash = row.pop("content_hash")
            if content_hash(row) != stored_hash or row["fingerprint"] != fingerprint:
                raise ValueError("corrupt or mixed ASR chunk")
            done[row["index"]] = row
        model = None
        generated = 0
        for index in range(total):
            if index in done:
                continue
            if args.max_chunks is not None and generated >= args.max_chunks:
                break
            if model is None:
                model = WhisperModel(str(model_path), device="cpu", compute_type=config["compute_type"],
                                     cpu_threads=config["cpu_threads"], num_workers=1, local_files_only=True)
            start = max(0, index * config["chunk_seconds"] - config["overlap_seconds"])
            end = min(duration, (index + 1) * config["chunk_seconds"] + config["overlap_seconds"])
            segments, _ = model.transcribe(audio[int(start * 16000):int(end * 16000)],
                language=config["language"], beam_size=config["beam_size"],
                condition_on_previous_text=config["condition_on_previous_text"], vad_filter=config["vad_filter"])
            row = {"index": index, "fingerprint": fingerprint, "start_seconds": start, "end_seconds": end,
                   "speaker": "UNVERIFIED", "status": "ASR_UNVERIFIED",
                   "segments": [{"start": s.start + start, "end": s.end + start, "text": s.text,
                                 "avg_logprob": s.avg_logprob, "no_speech_prob": s.no_speech_prob}
                                for s in segments]}
            write_json(output / "chunks" / f"{index:04d}.json", {**row, "content_hash": content_hash(row)})
            done[index] = row
            generated += 1
            write_json(output / "progress.json", {"completed_chunks": len(done), "total_chunks": total,
                "status": "ASR_UNVERIFIED", "complete_audio_coverage": len(done) == total})
            print(json.dumps({"completed_chunks": len(done), "total_chunks": total}), flush=True)
        write_json(output / "summary.json", {"fingerprint": fingerprint, "completed_chunks": len(done),
            "total_chunks": total, "complete_audio_coverage": len(done) == total,
            "human_reviewed": False, "training_admission": False,
            "overlap_note": "Chunks overlap by 2 seconds on each side; do not concatenate as unique speech.",
            "chunks": {str(i): content_hash(r) for i, r in done.items()}})


if __name__ == "__main__":
    main()
