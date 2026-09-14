"""Summarize completed frozen-protocol runs and the predeclared video-version gate."""
import json
import _bootstrap
from werewolf_sft.config import load_config
from werewolf_sft.evaluation import comparison
from werewolf_sft.io import ROOT, sha256_file, write_json
from werewolf_sft.runtime import load_cases

names = ("base_primary", "qlora_v01", "qlora_v02")
reports = {name: json.loads((ROOT / f"reports/runs/{name}/summary.json").read_text(encoding="utf-8"))
           for name in names}
comparison(reports["base_primary"], reports["qlora_v02"])
comparison(reports["qlora_v01"], reports["qlora_v02"])
review = json.loads((ROOT / "reports/dev_semantic_review_v02.json").read_text(encoding="utf-8"))
expected = {c["id"] for c in load_cases(load_config(ROOT / "configs/qlora_classic_v02.yaml"), "dev")}
if review["status"] != "complete" or {r["id"] for r in review["items"]} != expected or len(review["items"]) != len(expected):
    raise ValueError("all 23 dev cases must have a recorded semantic review")
for row in review["items"]:
    for run in ("qlora_v01", "qlora_v02"):
        if row["sources"][run] != sha256_file(ROOT / f"reports/runs/{run}/cases/{row['id']}.json"):
            raise ValueError("review source changed")
keys = ("format_valid", "action_legal", "action_match")
counts = {name: {key: round(sum(m["total"] * m[key + "_rate"] for m in report["summary"]["metrics"].values()))
                 for key in keys} for name, report in reports.items()}
for name in names:
    counts[name]["counterfactual_both_correct"] = reports[name]["summary"]["counterfactual"]["both_correct"]
deltas = {k: counts["qlora_v02"][k] - counts["qlora_v01"][k] for k in counts["qlora_v01"]}
reasons = [k + " declined by at least two cases" for k in keys if deltas[k] <= -2]
if deltas["counterfactual_both_correct"] < 0:
    reasons.append("counterfactual pair decline")
reasons += [r["id"] for r in review["items"] if r["new_critical_regression"]]
result = {"status": "complete", "protocol_fingerprint": reports["qlora_v02"]["protocol_fingerprint"],
          "counts_out_of_36": counts, "v02_minus_v01": deltas,
          "metric_denominators": {**{k: 36 for k in keys}, "counterfactual_both_correct": 4},
          "obvious_regression_gate_triggered": bool(reasons), "gate_reasons": reasons,
          "v03_may_be_considered": not reasons, "v03_created": False, "video_rows_in_v02": 0,
          "review_kind": review["review_kind"],
          "evidence_sha256": {name: sha256_file(ROOT / f"reports/runs/{name}/summary.json") for name in names},
          "review_sha256": sha256_file(ROOT / "reports/dev_semantic_review_v02.json"),
          "limitations": ["Single small deterministic benchmark; no statistical significance claim.",
                         "No independent human gameplay acceptance.",
                         "Training had six scheduled steps, three nonzero-learning-rate updates; tactics validation had one example.",
                         "Passing the no-obvious-regression gate does not establish expert quality or that every targeted defect was repaired."]}
write_json(ROOT / "reports/v02_acceptance_gate.json", result)
lines = ["# v0.1 Adapter vs v0.2-core Adapter", "",
         "2026-09-14：三阶段训练、36题同协议评测和23条dev模型语义复核已完成。v0.2自动指标较v0.1恢复，但仍未通过定向修复能力验收；新增严重规则/队伍信息回归触发预先记录的门禁，暂不构建v0.3-video。", "",
         "| 指标 | Base | v0.1 | v0.2-core |", "|---|---:|---:|---:|"]
labels = {"format_valid": "严格JSON结构", "action_legal": "合法动作",
          "action_match": "参考动作命中", "counterfactual_both_correct": "反事实双题同时命中"}
for key, label in labels.items():
    denominator = result["metric_denominators"][key]
    lines.append("| " + label + " | " + " | ".join(f"{counts[n][key]}/{denominator}" for n in names) + " |")
lines += ["", "v0.2合法动作与参考命中恢复至Base相同数量，尚未证明专项能力优于Base。严格单一参考动作不是所有合理策略的全集，但角色技能混淆、权限错误与无视合法信息属于实质缺陷。", "",
          "| 集合 | v0.1合法 / 命中 | v0.2合法 / 命中 |", "|---|---:|---:|"]
for suite in ("rules", "strategy", "counterfactual", "blind"):
    parts = []
    for name in ("qlora_v01", "qlora_v02"):
        m = reports[name]["summary"]["metrics"][suite]
        parts.append(f"{round(m['total'] * m['action_legal_rate'])}/{m['total']} / {round(m['total'] * m['action_match_rate'])}/{m['total']}")
    lines.append(f"| {suite} | " + " | ".join(parts) + " |")
lines += ["", "## 确认的局部收益与未修复项", "",
          "- 女巫救援等题的结构类型改善；猎人禁枪题少了已用枪/仅第一轮能开枪的编造；部分题开始核对公开主张与名单。",
          "- Blind预言家能根据站边冲突自主选择查验12；Blind票型关系题开始给出公开追问，但仍有私有分析误读与动作词错误。",
          "- 守卫连守/查验混淆、退水票权、屠边假设响应、动态改判、计划与既有结果区分、夜间公开泄露仍未系统修复。",
          "- 猎人反事实新增每轮查验/只能夜间查验的规则幻觉；狼队反事实把已确定队友降为未经查验的嫌疑，并放弃具体投票。四个dev案例触发门禁，是两组相关案例，不视为四个独立统计实验。",
          "- 自动public_leak_flag仍为0不代表无泄漏；逐题语义复核能看到夜间公开目标和用药信息。", "",
          "## 实验边界与证据", "",
          "- v0.2-core为86条原创修正样本、50族，42规则/22策略/22战术；阶段train/val为32/10、17/5、21/1。视频样本0，旧v0.1及视频独立池保持不变。",
          "- 同Base与revision，从Base重新开始；NF4/r8/alpha16、累积16、1epoch、5e-5。每阶段2步，总6步，其中3步非零学习率。零学习率预热仍积累Adam动量，不能声称前批梯度没有后续影响。",
          "- Classic训练消息经过专用裁剪，实际525～791 tokens，无过滤或截断；评测仍使用v0.1原输入/Prompt/生成/量化/评分协议，因此训练呈现格式与数据规模变化也属于实验变量，不能归因于单一原因。",
          "- 三方协议指纹均为" + result["protocol_fingerprint"] + "；36题无截断，恢复时复用了14题并核验SHA不变。没有重新生成既有题目。",
          "- 23条dev审核为本模型语义审核，非独立人工盲审；13条test只做冻结自动评分，没有用其文本生成修正数据。Tactics验证仅1例，未证明真实对局胜率或统计显著提升。",
          "- 原始回答/分数：reports/runs/{base_primary,qlora_v01,qlora_v02}；逐题复核：reports/dev_semantic_review_v02.*；门禁：reports/v02_acceptance_gate.json；恢复/权重核验：reports/v02_final_verification.json。",
          "", "## 下一步约束", "",
          "保留当前失败实验与全部权重；先基于dev记录诊断训练呈现、技能状态读取与优化日程，不改已冻结v0.2，不重训完成的阶段。视频候选继续单独审核，v0.3合并门禁保持关闭。"]
(ROOT / "reports/v01_vs_v02.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
review_lines = ["# v0.2全部23条dev语义复核", "", "状态：complete；model_semantic_review，非独立人工审核。原始回答SHA见同名JSON。评分和输出未因审核修改。", "",
                "| 案例 | 观察 | 新增严重回归 |", "|---|---|---|"]
review_lines += [f"| {r['id']} | {r['observation']} | {'YES' if r['new_critical_regression'] else 'NO'} |" for r in review["items"]]
(ROOT / "reports/dev_semantic_review_v02.md").write_text("\n".join(review_lines) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
