"""Generate or score static benchmarks; existing per-case results are resumable."""
import argparse
import json

import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.evaluation import summarize, comparison
from werewolf_sft.io import ROOT, content_hash, write_json, write_jsonl
from werewolf_sft.perspective import to_messages
from werewolf_sft.reporting import write_evaluation_report, write_comparison_report
from werewolf_sft.runtime import load_cases, protocol, adapter_digest, prepare_journal, append_prediction, load_generator, generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/qlora_classic.yaml")
    parser.add_argument("--adapter")
    parser.add_argument("--output", default="reports/runs/base_primary")
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all")
    parser.add_argument("--score-only", action="store_true")
    parser.add_argument("--compare-to")
    parser.add_argument("--report", help="Markdown report path; default inside this run")
    parser.add_argument("--comparison-report", default="reports/base_vs_qlora.md")
    args = parser.parse_args()
    config = load_config(ROOT / args.config)
    cases = load_cases(config, args.split)
    run = {"protocol": protocol(config, cases), "protocol_fingerprint": content_hash(protocol(config, cases)),
           "adapter_digest": adapter_digest(ROOT / args.adapter) if args.adapter else None}
    directory = ROOT / args.output
    predictions = prepare_journal(directory, run)
    done = {p["id"] for p in predictions}
    if any(p["run_fingerprint"] != content_hash(run) for p in predictions):
        raise ValueError("mixed prediction runs")
    if not args.score_only and len(done) < len(cases):
        write_json(directory / "progress.json", {"status": "loading_model", "completed": len(done), "total": len(cases)})
        try:
            model, tokenizer = load_generator(config, ROOT / args.adapter if args.adapter else None)
            for case in cases:
                if case["id"] in done:
                    continue
                result = generate(model, tokenizer, to_messages(case["scenario"], include_answer=False), config)
                prediction = {"id": case["id"], "run_fingerprint": content_hash(run), **result}
                append_prediction(directory, prediction)
                predictions.append(prediction)
                write_json(directory / "progress.json", {"status": "running", "completed": len(predictions), "total": len(cases)})
                print(json.dumps({"completed": len(predictions), "total": len(cases), "id": case["id"],
                                  "seconds": round(result["seconds"], 2)}, ensure_ascii=False), flush=True)
        except Exception as exc:
            write_json(directory / "failure.json", {"status": "failed", "error_type": type(exc).__name__,
                       "error": str(exc).replace(str(ROOT), "<workspace>"), "completed": len(predictions)})
            raise
    report = {**run, "summary": summarize(cases, predictions)}
    write_json(directory / "summary.json", report)
    write_jsonl(directory / "predictions.jsonl", predictions)
    write_evaluation_report(ROOT / args.report if args.report else directory / "report.md", report, cases, predictions)
    write_json(directory / "progress.json", {"status": report["summary"]["status"],
               "completed": len(predictions), "total": len(cases)})
    if args.compare_to:
        baseline = json.loads((ROOT / args.compare_to / "summary.json").read_text(encoding="utf-8"))
        write_json(directory / "comparison.json", comparison(baseline, report))
        write_comparison_report(ROOT / args.comparison_report, baseline, report)
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
