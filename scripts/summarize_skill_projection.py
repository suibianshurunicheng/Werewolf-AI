"""Rebuild paired dev statistics and full semantic report without model inference."""
import json
from collections import Counter, defaultdict
import _bootstrap
from werewolf_sft.evaluation import ACTION_TYPES, SCORING_VERSION, score_case, summarize
from werewolf_sft.io import ROOT, content_hash, read_jsonl, sha256_file, write_json
from werewolf_sft.skill_diagnostic import PACKET, OUTPUT


def loose_action_word(raw):
    # Diagnostic only: never alters strict action scoring or normalizes aliases.
    text = raw.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        text = text.removeprefix(fence + "json").removeprefix(fence).removesuffix(fence).strip()
    try:
        value = json.loads(text)
        action = value.get("action") if isinstance(value, dict) else None
        word = action.get("type") if isinstance(action, dict) else None
        return word if isinstance(word, str) else None
    except ValueError:
        return None


def main():
    spec = json.loads((ROOT / PACKET / "experiment.json").read_text(encoding="utf-8"))
    run = json.loads((ROOT / OUTPUT / "run.json").read_text(encoding="utf-8"))
    all_cases = {c["id"]: c for suite in ("rules", "strategy", "counterfactual", "blind")
                 for c in read_jsonl(ROOT / f"eval/{suite}.jsonl") if c["split"] == "dev"}
    review_path = ROOT / OUTPUT / "semantic_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {"items": []}
    reviews = {r["id"]: r for r in review["items"]}
    require = lambda value: None if value else (_ for _ in ()).throw(ValueError("diagnostic integrity mismatch"))
    require(len(reviews) == len(review["items"]) and set(reviews) <= set(spec["case_ids"]))
    rows, predictions = [], {"control": [], "treatment": []}
    for identifier in spec["case_ids"]:
        treatment_path = ROOT / OUTPUT / "cases" / (identifier + ".json")
        if not treatment_path.exists():
            continue
        case = all_cases[identifier]
        row = {"id": identifier, "role": case["scenario"]["role"], "stage": case["scenario"]["stage"], "pair_id": case["pair_id"]}
        for side, path in (("control", ROOT / "reports/runs/qlora_v02/cases" / (identifier + ".json")), ("treatment", treatment_path)):
            pred = json.loads(path.read_text(encoding="utf-8"))
            require(pred["run_fingerprint"] == content_hash(run if side == "treatment" else spec["source_run"]))
            predictions[side].append(pred)
            word = loose_action_word(pred["raw_response"])
            row[side] = {"strict": score_case(case, pred["raw_response"], pred["truncated"]),
                         "raw_action_word": word, "unknown_raw_action_word": word is not None and word not in ACTION_TYPES,
                         "prediction_sha256": sha256_file(path)}
            if identifier in reviews:
                require(reviews[identifier]["sources"][side] == sha256_file(path))
        row["semantic"] = reviews.get(identifier)
        rows.append(row)
    fields = ("format_valid", "action_legal", "action_match", "unknown_action_type", "public_leak_flag", "truncated")
    def aggregate(group):
        result = {"count": len(group)}
        for side in predictions:
            result[side] = {key: sum(r[side]["strict"][key] for r in group) for key in fields}
            result[side]["unknown_raw_action_word"] = sum(r[side]["unknown_raw_action_word"] for r in group)
            result[side]["raw_word_unavailable"] = sum(r[side]["raw_action_word"] is None for r in group)
            result[side]["unknown_words"] = dict(Counter(r[side]["raw_action_word"] for r in group if r[side]["unknown_raw_action_word"]))
        result["semantic_changes"] = dict(Counter(r["semantic"]["change"] for r in group if r["semantic"]))
        return result
    by_role = {role: aggregate([r for r in rows if r["role"] == role]) for role in sorted({r["role"] for r in rows})}
    semantic_errors = {}
    for key in ("role_skill", "state_reading", "permission", "team_knowledge", "public_private", "night_leak"):
        rated = [r["semantic"]["errors"][key] for r in rows if r["semantic"] and all(v is not None for v in r["semantic"]["errors"][key])]
        semantic_errors[key] = {"paired_rated": len(rated), "control_error": sum(x[0] for x in rated), "treatment_error": sum(x[1] for x in rated)}
    selected = [all_cases[r["id"]] for r in rows]
    pair_summary = {side: summarize(selected, preds)["counterfactual"] for side, preds in predictions.items()} if selected else {}
    report = {"status": "complete" if len(rows) == len(reviews) == 23 else "partial",
              "experiment_id": spec["experiment_id"], "scoring_version": SCORING_VERSION,
              "expected": 23, "compared": len(rows), "reviewed": len(reviews), "summary": aggregate(rows),
              "by_role": by_role, "semantic_errors": semantic_errors, "counterfactual": pair_summary,
              "rows": rows, "branch": review.get("branch", "pending"), "conclusion": review.get("conclusion", "尚未完成全量审查"),
              "held_out_claim": False, "review_kind": "model_semantic_review_not_independent_human"}
    write_json(ROOT / OUTPUT / "paired_analysis.json", report)
    lines = ["# v02_skill_projection_v0.1 正式诊断报告", "", f"状态：{report['status']}；已比较{len(rows)}/23，语义审核{len(reviews)}/23。仅dev探索，非held-out能力验收。", "", report["conclusion"], "",
             "## 实验控制", "", "冻结输入包和v0.2 Tactics final；只投影skill_state。系统提示、布局、角色、任务、私有/公开历史、原strict-actions-v1.1、生成参数及权重均保持一致。旧输出作为控制，处理输出另目录逐题原子保存。没有用test答案调参，没有重训或混入视频。", "",
             "## 自动动作指标", "", "strict action score在本报告指合法且命中原参考动作（action_match）；合法动作单列。未知动作token/word指action.type字符串，不是模型词表中的token计数。原严格解析失败的输出不会计入unknown_action_type，另列宽松JSON提取的unknown raw action word，二者不改评分、不做别名纠正。", "",
             "|指标|控制|投影|", "|---|---:|---:|"]
    for key in fields + ("unknown_raw_action_word", "raw_word_unavailable"):
        lines.append(f"|{key}|{report['summary']['control'][key]}/{len(rows)}|{report['summary']['treatment'][key]}/{len(rows)}|")
    lines += ["", "未知词分布：" + json.dumps({s: report["summary"][s]["unknown_words"] for s in predictions}, ensure_ascii=False), "",
              "## 角色分组", "", "|角色/题数|合法 控制→投影|严格命中 控制→投影|语义变化|", "|---|---|---|---|"]
    for role, g in by_role.items():
        lines.append(f"|{role}/{g['count']}|{g['control']['action_legal']}→{g['treatment']['action_legal']}|{g['control']['action_match']}→{g['treatment']['action_match']}|{json.dumps(g['semantic_changes'], ensure_ascii=False)}|")
    lines += ["", "## 语义错误复核", "", "下表是模型语义审核，非独立专家盲审；仅统计两侧均可评估的维度，null不按正确计。动作拼写单独评分；语义技能、状态、权限错误依据原回答判定。", "", "|维度|配对可评估|控制错误|投影错误|", "|---|---:|---:|---:|"]
    for key, g in semantic_errors.items():
        lines.append(f"|{key}|{g['paired_rated']}|{g['control_error']}|{g['treatment_error']}|")
    lines += ["", "public_leak_flag是原有限正则；夜间泄漏由逐题语义审核判断，不能把正则0理解成无泄漏。", "", "## 反事实", "", json.dumps(pair_summary, ensure_ascii=False), "", "只含dev守卫/猎人/狼队三对，不含test对；动作变化本身不代表合理动态调整。以下逐题内容保留配对方向及错误。", "", "## 全部案例（不筛选）", ""]
    for row in rows:
        lines += ["### " + row["id"], "", f"角色：{row['role']}；{row['stage']}；pair={row['pair_id']}。", "",
                  "动作：" + json.dumps({s: row[s]["strict"].get("parsed_action", {"parse_error": row[s]["strict"].get("parse_error")}) for s in predictions}, ensure_ascii=False), "",
                  (row["semantic"]["change"] + "：" + row["semantic"]["observation"]) if row["semantic"] else "语义审核待完成。", ""]
    lines += ["## 证据与限制", "", "原始回答、输入指纹和逐题SHA见本目录cases、run.json、paired_analysis.json及semantic_review.json。skill_state裁剪是一个组合干预（包括序列长度变化），不能区分每个字段的因果贡献。当前权重上的dev结果不能证明训练覆盖或训练日程是唯一主因；后续分支的未执行实验必须明确记为尚未验证。", ""]
    (ROOT / OUTPUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "compared", "reviewed", "summary", "counterfactual", "branch")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
