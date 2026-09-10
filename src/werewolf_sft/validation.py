"""Schema, perspective, role/phase legality and split-contamination checks."""
from __future__ import annotations

import json
import re
from collections import Counter

from .io import ROOT, canonical, content_hash
from .perspective import player_view
from .rules import BOARDS, RULE_VERSION, STAGES, effective_role, legal_actions

REQUIRED = {"id", "scenario_id", "dataset_version", "rule_version", "board", "seat", "role", "stage", "round",
            "private_info", "public_info", "skill_state", "task", "analysis", "identity_reads", "strategy", "action",
            "public_response", "tactical_tags", "quality_score", "source", "review", "evidence_ids", "training_stage",
            "wolf_pit", "god_pit", "round_assessment"}
SKILL_DEFAULTS = dict(antidote_available=False, poison_available=False, potion_used_tonight=False,
                      checked_seats=[], last_guard_target=None, mimic_used=False, mimic_role=None,
                      mimic_round=None, knife_enabled=False, extra_knife_available=False,
                      selected_knife_target=None, hunter_can_shoot=False, shot_used=False,
                      last_words_allowed=False)
FACT_KINDS = {"wolf_team", "check_result", "mimic_result", "witch_knife"}
LEAK_PATTERNS = (r"全部(?:玩家)?(?:真实)?身份[：:]", r"裁判(?:全局|底牌|视角)",
                 r"hidden_info|true_roles|ground_truth", r"(?:我的|我们)(?:狼队友|狼队|四狼)(?:是|为|有)")


def validate_row(row, schema=True):
    errors = []
    if set(row) != REQUIRED:
        return ["unexpected/missing keys: " + str(sorted(set(row) ^ REQUIRED))]
    if schema:
        from jsonschema import Draft202012Validator
        spec = json.loads((ROOT / "data/schemas/sample.schema.json").read_text(encoding="utf-8"))
        errors += [f"schema:{'/'.join(map(str, e.path))}: {e.message}"
                   for e in Draft202012Validator(spec).iter_errors(row)]
        if errors:
            return errors
    if row["board"] not in BOARDS or row["role"] not in BOARDS.get(row["board"], {}):
        return errors + ["role not in board"]
    if row["rule_version"] != RULE_VERSION or row["stage"] not in STAGES:
        errors.append("unknown rules/stage")
    own, public, state = row["seat"], row["public_info"], row["skill_state"]
    alive = public["alive"]
    if len(alive) != len(set(alive)) or any(s not in range(1, 13) for s in alive):
        errors.append("invalid alive seats")
    for name in ("candidates", "sheriff_registered"):
        if len(public[name]) != len(set(public[name])) or any(s not in range(1, 13) for s in public[name]):
            errors.append("invalid election seats")
    if any(s not in alive for s in public["candidates"]):
        errors.append("dead candidate")
    if set(state) != set(SKILL_DEFAULTS):
        return errors + ["unknown or missing skill state"]
    if state["mimic_used"]:
        if row["role"] != "awakened_hidden_wolf" or state["mimic_role"] not in BOARDS["mirror_12"]:
            errors.append("invalid mimic state")
        if state["mimic_round"] is None or not 1 <= state["mimic_round"] <= row["round"]:
            errors.append("invalid mimic time")
    elif state["mimic_role"] is not None or state["mimic_round"] is not None:
        errors.append("mimic metadata without mimic")
    role = effective_role(row) if not errors else row["role"]
    if state["antidote_available"] and row["role"] != "witch":
        errors.append("unauthorized antidote")
    if state["poison_available"] and role != "witch":
        errors.append("unauthorized poison")
    if state["last_guard_target"] is not None and role != "guard":
        errors.append("unauthorized guard memory")
    if state["checked_seats"] and role not in {"seer", "mirror_girl"}:
        errors.append("unauthorized check history")
    if (state["hunter_can_shoot"] or state["shot_used"]) and role != "hunter":
        errors.append("unauthorized hunter state")
    if state["extra_knife_available"] and not (row["role"] == "awakened_hidden_wolf" and role == "werewolf" and state["knife_enabled"]):
        errors.append("unauthorized extra knife")
    if state["knife_enabled"] and row["role"] != "awakened_hidden_wolf":
        errors.append("knife takeover only for hidden wolf")
    event_ids = set()
    for event in public["events"]:
        if event["round"] > row["round"]:
            errors.append("future public event")
        if event["id"] in event_ids:
            errors.append("duplicate evidence id")
        event_ids.add(event["id"])
        if event["kind"] != "speech" and re.search(r"(?:真实身份|底牌)[：:]", event["text"]):
            errors.append("dark-role reveal in public facts")
    team_targets = []
    for fact in row["private_info"]["facts"]:
        kind, target = fact["kind"], fact["target"]
        if fact["id"] in event_ids:
            errors.append("duplicate evidence id")
        event_ids.add(fact["id"])
        if fact["round"] > row["round"]:
            errors.append("future private fact")
        if kind == "wolf_team":
            team_targets.append(target)
            if row["role"] != "werewolf" or fact["value"] != "werewolf" or target == own:
                errors.append("unauthorized wolf-team identity")
        elif kind == "check_result":
            if role not in {"seer", "mirror_girl"} or target == own:
                errors.append("unauthorized check")
            allowed = {"good", "wolves"} if role == "seer" else set(BOARDS["mirror_12"])
            if fact["value"] not in allowed:
                errors.append("check result type does not match role")
            if target not in state["checked_seats"]:
                errors.append("check fact missing from skill history")
        elif kind == "mimic_result":
            if row["role"] != "awakened_hidden_wolf" or not state["mimic_used"] or target == own:
                errors.append("unauthorized mimic result")
            elif fact["value"] != state["mimic_role"] or fact["round"] != state["mimic_round"]:
                errors.append("mimic fact disagrees with state")
        elif kind == "witch_knife":
            if row["role"] != "witch" or fact["value"] != "attacked":
                errors.append("unauthorized witch notice")
            if fact["round"] == row["round"] and not state["antidote_available"]:
                errors.append("new knife notice after antidote spent")
        else:
            errors.append("unknown fact kind")
    max_team = 3 if row["board"] == "classic_12" else 2
    if len(team_targets) != len(set(team_targets)) or len(team_targets) > max_team:
        errors.append("too many/duplicate known wolves")
    if row["role"] == "awakened_hidden_wolf" and any(f["kind"] == "wolf_team" for f in row["private_info"]["facts"]):
        errors.append("hidden wolf cannot know small-wolf team")
    if not set(row["evidence_ids"]) <= event_ids:
        errors.append("analysis cites invisible evidence")
    text = canonical(player_view(row))
    if any(re.search(p, text, re.I) for p in LEAK_PATTERNS[:3]):
        errors.append("omniscient input marker")
    if row["role"] in {"werewolf", "awakened_hidden_wolf"} and any(re.search(p, row["public_response"]) for p in LEAK_PATTERNS[3:]):
        errors.append("wolf-team confession in public response")
    if any(s in row["public_response"] for s in ("PRIVATE ANALYSIS", "PRIVATE STRATEGY", "【局势分析】", "【当前策略】")):
        errors.append("private section in public response")
    if not errors and row["action"] not in legal_actions(row):
        errors.append("illegal target/action/phase/skill")
    return errors


def validate_dataset(rows):
    issues, ids, inputs = [], set(), set()
    for row in rows:
        issues += [f"{row.get('id', '?')}: {error}" for error in validate_row(row)]
        if row.get("id") in ids:
            issues.append("duplicate id: " + row["id"])
        ids.add(row.get("id"))
        if not (REQUIRED - set(row)):
            digest = content_hash(player_view(row))
            if digest in inputs:
                issues.append("duplicate input: " + row["id"])
            inputs.add(digest)
    return issues


def assert_disjoint(train, evaluation):
    train_groups = {r["scenario_id"] for r in train}
    train_inputs = {content_hash(player_view(r)) for r in train}
    for row in evaluation:
        if row["scenario_id"] in train_groups or content_hash(player_view(row)) in train_inputs:
            raise ValueError("train/eval contamination: " + row["id"])


def require_silver_reviews(row):
    review = row["review"]
    if not review["rule_checked"] or not review["perspective_checked"]:
        raise ValueError("silver checks incomplete")
    if len(set(review["critic_models"])) < 2 or not review["human_approved"]:
        raise ValueError("silver requires two distinct critics and human approval")
    if row["quality_score"] < 4:
        raise ValueError("silver quality below 4/5")
