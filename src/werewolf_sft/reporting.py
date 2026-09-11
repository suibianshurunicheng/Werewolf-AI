"""Human-readable reports derived only from completed prediction artifacts."""
import statistics
from .evaluation import summarize, score_case, comparison
from .io import write_json


def write_evaluation_report(path, report, cases, predictions):
    summary = report["summary"]
    lines = [
        "# " + ("QLoRA Benchmark" if report["adapter_digest"] else "Base Model Baseline"),
        "", f"状态：{summary['status']}；完成 {summary['completed_cases']}/{summary['expected_cases']} 题。",
        f"Base：{report['protocol']['model']}；revision：{report['protocol']['revision']}。",
        f"协议指纹：{report['protocol_fingerprint']}。Adapter：{report['adapter_digest'] or '无'}。",
        "", "下列为固定静态题的自动指标；不代表真实对局胜率，也不替代人工策略评价。",
        "动作匹配只检查预先冻结的参考动作，不能单独证明发言策略正确。泄漏为有限规则标记，0不证明无泄漏。",
        "", "| 集合 | 题数 | JSON有效 | 动作合法 | 参考动作匹配 | 未知动作词 | 截断 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for suite, m in summary["metrics"].items():
        lines.append(f"| {suite} | {m['total']} | {m['format_valid_rate']:.1%} | {m['action_legal_rate']:.1%} | {m['action_match_rate']:.1%} | {m['unknown_action_type_rate']:.1%} | {m['truncated_rate']:.1%} |")
    lines += ["", "未知动作词是接口兼容问题，不能直接当成规则不懂。当前v0.1 Prompt未枚举动作词典；策略提升必须另做语义审核。"]
    if predictions:
        lines += ["", f"观测生成速度中位数：{statistics.median(p['output_tokens_per_second'] for p in predictions):.2f} tokens/s。",
                  f"观测PyTorch最大已分配显存：{max(p['peak_vram_mib'] for p in predictions):.1f} MiB；不含桌面和驱动占用。",
                  f"反事实两题同时命中：{summary['counterfactual']['both_correct']}/{summary['counterfactual']['pairs']}。",
                  "", "人工策略质量：待复核。正式训练以前仅分析dev错误，test不得用于修正数据。"]
    for split in ("dev", "test"):
        selected = [c for c in cases if c["split"] == split]
        ids = {c["id"] for c in selected}
        split_summary = summarize(selected, [p for p in predictions if p["id"] in ids])
        lines += ["", f"## {split} 自动结果", ""]
        lines += [f"- {suite}：参考动作匹配 {m['action_match_rate']:.1%}（{m['total']} 题）"
                  for suite, m in split_summary["metrics"].items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    by_id = {p["id"]: p for p in predictions}
    write_json(path.with_suffix(".cases.json"), [
        {"id": c["id"], "split": c["split"], "suite": c["suite"],
         "score": score_case(c, by_id[c["id"]]["raw_response"], by_id[c["id"]]["truncated"])}
        for c in cases if c["id"] in by_id])


def write_comparison_report(path, baseline, adapted):
    delta = comparison(baseline, adapted)
    lines = ["# Base vs QLoRA", "", "相同Base revision、题目、输入、量化和生成协议。正值表示百分比上升。",
             "仅自动指标；专项策略提升仍需盲审和人工对局验证。", "",
             "| 集合 | JSON有效变化 | 合法动作变化 | 参考动作变化 |", "|---|---:|---:|---:|"]
    for suite, d in delta.items():
        lines.append(f"| {suite} | {d['format_valid_rate']:+.1%} | {d['action_legal_rate']:+.1%} | {d['action_match_rate']:+.1%} |")
    lines += ["", "不能把较低Loss或JSON改善等同于狼人杀策略提升。"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
