"""Strict output validation; separate automated metrics and human review."""
import json
import math
import re
from collections import defaultdict

from .rules import legal_actions, TARGET_ACTIONS

SCORING_VERSION = "strict-actions-v1.1"
ACTION_TYPES = TARGET_ACTIONS | {"pass", "speak", "explode", "run_sheriff", "withdraw", "tear_badge"}

OUTPUT_KEYS = {"analysis", "identity_reads", "wolf_pit", "god_pit", "round_assessment",
               "strategy", "action", "public_response"}


def parse_response(text):
    text = text.strip()
    fence = chr(96) * 3
    if text.startswith(fence + "json") and text.endswith(fence):
        text = text[7:-3].strip()
    elif text.startswith(fence) and text.endswith(fence):
        text = text[3:-3].strip()
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != OUTPUT_KEYS:
        raise ValueError("response must contain exactly eight output fields")
    for key in OUTPUT_KEYS - {"identity_reads", "action"}:
        if not isinstance(value[key], str):
            raise ValueError("text field expected: " + key)
    if not isinstance(value["identity_reads"], list):
        raise ValueError("identity_reads must be a list")
    for read in value["identity_reads"]:
        if not isinstance(read, dict) or set(read) != {"seat", "assessment", "confidence"}:
            raise ValueError("invalid identity read")
        if type(read["seat"]) is not int or not 1 <= read["seat"] <= 12 or not isinstance(read["assessment"], str):
            raise ValueError("invalid identity seat/assessment")
        if type(read["confidence"]) not in {int, float} or not math.isfinite(read["confidence"]) or not 0 <= read["confidence"] <= 1:
            raise ValueError("invalid identity confidence")
    action = value["action"]
    if not isinstance(action, dict) or set(action) != {"type", "target"} or not isinstance(action["type"], str):
        raise ValueError("invalid action")
    if action["target"] is not None and (type(action["target"]) is not int or not 1 <= action["target"] <= 12):
        raise ValueError("invalid target")
    return value


def public_leakage(payload, role):
    text = payload["public_response"]
    if any(marker in text for marker in ("PRIVATE ANALYSIS", "PRIVATE STRATEGY", "【局势分析】", "【当前策略】")):
        return True
    return role in {"werewolf", "awakened_hidden_wolf"} and bool(
        re.search(r"(我的|我们)(狼队友|狼队|四狼)(是|为|有)", text))


def score_case(case, raw, truncated=False):
    result = {"format_valid": False, "action_legal": False, "action_match": False,
              "unknown_action_type": False,
              "public_leak_flag": False, "concept_hits": 0,
              "concept_total": len(case["expected"]["concepts"]), "truncated": bool(truncated),
              "human_review": "pending"}
    try:
        payload = parse_response(raw)
    except (ValueError, TypeError) as exc:
        result["parse_error"] = str(exc)
        return result
    result["format_valid"] = not truncated
    result["unknown_action_type"] = not truncated and payload["action"]["type"] not in ACTION_TYPES
    result["action_legal"] = not truncated and payload["action"] in legal_actions(case["scenario"])
    result["action_match"] = result["action_legal"] and payload["action"] in case["expected"]["actions"]
    result["public_leak_flag"] = public_leakage(payload, case["scenario"]["role"])
    diagnostic = payload["analysis"] + payload["strategy"] + payload["public_response"] + payload["round_assessment"]
    result["concept_hits"] = sum(word in diagnostic for word in case["expected"]["concepts"])
    result["parsed_action"] = payload["action"]
    return result


def summarize(cases, predictions):
    by_id = {p["id"]: p for p in predictions}
    if len(by_id) != len(predictions):
        raise ValueError("duplicate prediction ids")
    if set(by_id) - {c["id"] for c in cases}:
        raise ValueError("unknown prediction ids")
    groups, pairs = defaultdict(list), defaultdict(list)
    for case in cases:
        pred = by_id.get(case["id"])
        score = score_case(case, pred["raw_response"], pred.get("truncated", False)) if pred else score_case(case, "")
        groups[case["suite"]].append(score)
        if case["pair_id"]:
            pairs[case["pair_id"]].append(score)
    metrics = {}
    for suite, scores in groups.items():
        metrics[suite] = {"total": len(scores), **{
            key + "_rate": sum(bool(row[key]) for row in scores) / len(scores)
            for key in ("format_valid", "action_legal", "action_match", "unknown_action_type", "public_leak_flag", "truncated")
        }}
    paired = [pair for pair in pairs.values() if len(pair) == 2]
    return {
        "status": "complete" if len(predictions) == len(cases) else "partial",
        "expected_cases": len(cases), "completed_cases": len(predictions), "metrics": metrics,
        "counterfactual": {
            "pairs": len(paired),
            "both_correct": sum(all(s["action_match"] for s in p) for p in paired),
            "action_changed": sum(all(s["format_valid"] for s in p) and
                                  p[0].get("parsed_action") != p[1].get("parsed_action") for p in paired),
        },
        "human_strategy_quality": "pending",
        "note": "Automated action metrics are not a full Werewolf reasoning score.",
    }


def comparison(baseline, adapted):
    if baseline["protocol_fingerprint"] != adapted["protocol_fingerprint"]:
        raise ValueError("baseline and adapter protocols differ")
    if baseline.get("scoring_version") != SCORING_VERSION or adapted.get("scoring_version") != SCORING_VERSION:
        raise ValueError("scoring versions differ; re-score both saved runs using --score-only")
    if baseline["summary"]["status"] != "complete" or adapted["summary"]["status"] != "complete":
        raise ValueError("comparison requires complete evaluations")
    return {suite: {key: adapted["summary"]["metrics"][suite][key] - value
                    for key, value in metrics.items() if key.endswith("_rate")}
            for suite, metrics in baseline["summary"]["metrics"].items()}
