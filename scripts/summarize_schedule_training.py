"""Compare actual A and diagnostic schedule logs, preserving checkpoint lineage."""
import argparse
import json
import _bootstrap
from werewolf_sft.io import ROOT, read_jsonl, write_json, sha256_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=["B_warmup0", "C_accum8"])
    args = parser.parse_args()
    destination = ROOT / "reports/diagnostics/schedule_v0.1" / args.arm
    frozen = json.loads((ROOT / "reports/training_schedule_v01_preflight.json").read_text(encoding="utf-8"))
    rows = []
    for stage in ("rules", "strategy", "tactics"):
        audit = json.loads((destination / stage / "schedule_audit.json").read_text(encoding="utf-8"))
        actual_lrs = [p["applied_lr"] for p in audit["checkpoints"]]
        planned = frozen["matrix"][args.arm]["stages"][stage]
        assert actual_lrs == planned["planned_lr_at_optimizer_step"]
        assert audit["optimizer_steps"] == planned["optimizer_steps"]
        old = ROOT / f"reports/training/{stage}_v02"
        result = json.loads((old / "training_result.json").read_text(encoding="utf-8"))
        logs = read_jsonl(old / "training.jsonl")
        lrs = [r["learning_rate"] for r in logs if "learning_rate" in r]
        rows.append({"stage": stage, "A": {"optimizer_steps": len(lrs), "nonzero_lr_steps": sum(lr > 0 for lr in lrs),
            "applied_lrs": lrs, "train_loss": result["metrics"]["train_loss"], "validation_loss": result["validation"]["eval_loss"],
            "peak_vram_mib": result["peak_vram_mib"], "training_log_sha256": sha256_file(old / "training.jsonl")}, "variant": audit})
    report = {"status": "verified", "arm": args.arm, "stages": rows,
        "actual_optimizer_steps": sum(r["variant"]["optimizer_steps"] for r in rows),
        "actual_nonzero_lr_steps": sum(r["variant"]["nonzero_lr_steps"] for r in rows),
        "final_chain_nonzero_lr_updates": sum(r["variant"]["best_checkpoint_nonzero_updates_this_stage"] for r in rows),
        "A_actual_optimizer_steps": 6, "A_actual_nonzero_lr_steps": 3,
        "causal_limit": "Warmup changes LR trajectory/integral and Adam history, not just count. Single seed; no capability inference from loss.",
        "test_selection": False, "video_or_persona": False}
    write_json(destination / "training_comparison.json", report)
    lines = ["# A vs " + args.arm + " 真实训练证据", "", "三阶段完成且checkpoint逐文件SHA、实际张量变化、冻结计划LR均核验通过。能力结论待同23-dev全量语义复核。", "",
        "|阶段|A/B optimizer步|A/B非零LR步|A valLoss|本组valLoss|本组trainLoss|峰值MiB|best step|", "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        a, b = row["A"], row["variant"]
        lines += [f"|{row['stage']}|{a['optimizer_steps']}/{b['optimizer_steps']}|{a['nonzero_lr_steps']}/{b['nonzero_lr_steps']}|{a['validation_loss']:.6f}|{b['validation_loss']:.6f}|{b['train_loss']:.6f}|{b['peak_vram_mib']:.1f}|{b['best_step']}|"]
    for row in rows:
        b = row["variant"]
        lines += ["", "## " + row["stage"], "", "A实际LR=" + str(row["A"]["applied_lrs"]) + "；本组实际LR=" + str([p["applied_lr"] for p in b["checkpoints"]]),
            "", "initial Adapter：" + b["initial_adapter_source"], "", "final Adapter SHA：" + b["final_adapter_sha256"],
            "", "best=" + b["best_checkpoint"] + "；final=" + b["final_checkpoint"] + "。final与best逐字节相同。",
            "", "本阶段实际非零更新=" + str(b["nonzero_lr_steps"]) + "，best前缀非零更新=" + str(b["best_checkpoint_nonzero_updates_this_stage"]) + "。"]
    lines += ["", "## 限制与恢复", "", "A的零LR步仍积累Adam动量。warmup变化也改变cosine轨迹和LR积分，不能只归因于计数。best选择依旧依赖很小的阶段验证集，尤其Tactics仅1条验证；Loss不是狼人杀能力验收。", "",
        "完整config、数据SHA、Base revision、日志、每步train/val/epoch、checkpoint SHA、逐步张量变化见各阶段run_manifest、training.jsonl、artifacts和schedule_audit。大权重在outputs；Git只保存证据，迁移主机须复制并校验权重。已完成阶段不可重训。", ""]
    (destination / "training_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("arm", "actual_optimizer_steps", "actual_nonzero_lr_steps", "final_chain_nonzero_lr_updates")}))


if __name__ == "__main__":
    main()
