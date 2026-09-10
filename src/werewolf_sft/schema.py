"""Single source for the JSON Schema and starter records."""
from __future__ import annotations

import copy

from .rules import BOARDS, ROLE_ZH, RULE_VERSION, STAGES, action
from .validation import REQUIRED, SKILL_DEFAULTS


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required, "additionalProperties": False}


def array(items, unique=False):
    return {"type": "array", "items": items, "uniqueItems": unique}


def sample_schema():
    seat = {"type": "integer", "minimum": 1, "maximum": 12}
    nullable_seat = {"anyOf": [seat, {"type": "null"}]}
    string = {"type": "string"}
    nonempty = {"type": "string", "minLength": 1}
    round_spec = {"type": "integer", "minimum": 1, "maximum": 50}
    fact = obj(dict(id=nonempty, kind={"enum": ["wolf_team", "check_result", "mimic_result", "witch_knife"]},
                    target=seat, value=nonempty, round=round_spec))
    event = obj(dict(id=nonempty, kind={"enum": ["speech", "vote", "death", "moderator"]},
                     round=round_spec, actor=nullable_seat, target=nullable_seat, text=nonempty))
    skills = {}
    for k, value in SKILL_DEFAULTS.items():
        if isinstance(value, bool):
            skills[k] = {"type": "boolean"}
        elif isinstance(value, list):
            skills[k] = array(seat, True)
        elif k == "mimic_role":
            skills[k] = {"enum": [None] + list(ROLE_ZH)}
        elif k == "mimic_round":
            skills[k] = {"anyOf": [round_spec, {"type": "null"}]}
        else:
            skills[k] = nullable_seat
    fields = dict(
        id=nonempty, scenario_id=nonempty, dataset_version={"pattern": r"^dataset_v0\.[123]$", "type": "string"},
        rule_version={"const": RULE_VERSION}, board={"enum": list(BOARDS)}, seat=seat,
        role={"enum": list(ROLE_ZH)}, stage={"enum": sorted(STAGES)}, round=round_spec,
        private_info=obj({"facts": array(fact)}),
        public_info=obj(dict(alive=array(seat, True), sheriff=nullable_seat, candidates=array(seat, True),
                             sheriff_registered=array(seat, True), events=array(event))),
        skill_state=obj(skills), task=nonempty, analysis=nonempty, strategy=nonempty,
        identity_reads=array(obj(dict(seat=seat, assessment=nonempty, confidence={"type": "number", "minimum": 0, "maximum": 1}))),
        wolf_pit=string, god_pit=string, round_assessment=nonempty,
        action=obj(dict(type={"enum": ["pass", "speak", "vote", "check", "poison", "heal", "guard", "mimic", "knife",
                                       "extra_knife", "shoot", "transfer_badge", "tear_badge", "run_sheriff", "withdraw", "explode"]}, target=nullable_seat)),
        public_response=string, tactical_tags=array(nonempty, True),
        quality_score={"type": "number", "minimum": 0, "maximum": 5},
        source=obj(dict(kind={"enum": ["original_synthetic", "licensed_match", "teacher_generated"]},
                        license=nonempty, reference_urls=array(string), author=nonempty)),
        review=obj(dict(rule_checked={"type": "boolean"}, perspective_checked={"type": "boolean"},
                        critic_models=array(nonempty, True), human_approved={"type": "boolean"}, notes=string)),
        evidence_ids=array(nonempty, True), training_stage={"enum": ["rules", "strategy", "tactics"]},
    )
    assert set(fields) == REQUIRED
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Werewolf player SFT record", **obj(fields)}


def new_sample(identifier, role="villager", seat=3, stage="day_speech", round_no=1, training_stage="rules"):
    return dict(
        id=identifier, scenario_id=identifier, dataset_version="dataset_v0.1", rule_version=RULE_VERSION,
        board="classic_12", seat=seat, role=role, stage=stage, round=round_no,
        private_info={"facts": []},
        public_info=dict(alive=list(range(1, 13)), sheriff=None, candidates=[], sheriff_registered=[], events=[]),
        skill_state=copy.deepcopy(SKILL_DEFAULTS), task="根据当前信息完成本阶段行动。",
        analysis="信息尚不足以确定他人底牌。", identity_reads=[], wolf_pit="未确定", god_pit="不公开猜测神职位置",
        round_assessment="本轮仍需结合公开死亡和票型判断，不能按未知身份计算确定轮次。",
        strategy="先收集可核对证据。", action=action("speak" if stage == "day_speech" else "pass"),
        public_response="请先把判断依据讲清楚，我会结合发言和投票再判断。" if stage == "day_speech" else "",
        tactical_tags=[], quality_score=4,
        source=dict(kind="original_synthetic", license="CC-BY-4.0", reference_urls=[], author="Werewolf-Classic contributors / Codex"),
        review=dict(rule_checked=False, perspective_checked=False, critic_models=[], human_approved=False,
                    notes="作者设计的合成种子；质量分为作者自评，并非独立 Critic 或人工复核。"),
        evidence_ids=[], training_stage=training_stage,
    )


def add_event(row, text, actor=None, kind="speech", target=None, round_no=None):
    identifier = f"e{len(row['public_info']['events']) + 1}"
    row["public_info"]["events"].append(dict(id=identifier, kind=kind, round=round_no or row["round"],
                                             actor=actor, target=target, text=text))
    row["evidence_ids"].append(identifier)


def add_fact(row, kind, target, value, round_no=None):
    identifier = f"p{len(row['private_info']['facts']) + 1}"
    row["private_info"]["facts"].append(dict(id=identifier, kind=kind, target=target, value=value, round=round_no or row["round"]))
    row["evidence_ids"].append(identifier)

