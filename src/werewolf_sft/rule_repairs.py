"""Small authored v0.2 rule pairs; no benchmark answers or seat permutations."""
import copy

from .rules import action
from .schema import add_fact, new_sample


def visible_changes(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        return [p for k in a for p in visible_changes(a[k], b[k], f"{path}.{k}".strip("."))]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [p for i in range(len(a)) for p in visible_changes(a[i], b[i], f"{path}.{i}")]
    return [] if a == b else [path]


def rule_repair_batch():
    rows, pairs = [], []

    def base(role, stage="night", round_no=2):
        r = new_sample("pending", role, seat=2, stage=stage, round_no=round_no)
        r.update(dataset_version="dataset_v0.2", wolf_pit="本题没有其他玩家的确定阵营信息。",
                 god_pit="仅使用自己的合法角色能力，不推定其他神职。", public_response="")
        r["review"]["notes"] = "原创规则修正候选；作者自评，未独立人工复核；非视频Gold。"
        return r

    def answer(r, kind, target, reason, public=""):
        r.update(action=action(kind, target), analysis=reason, strategy=reason,
                 public_response=public, round_assessment=f"第{r['round']}轮，当前{r['stage']}。" + reason)
        return r

    def pair(name, family, a, b, basis):
        from .perspective import player_view
        for label, row in zip(("a", "b"), (a, b)):
            row.update(id=f"v02-rule-{name}-{label}", scenario_id="v02-rules-" + family,
                       tactical_tags=["rule_repair", name, "paired_condition"])
            rows.append(row)
        pairs.append({"id": name, "scenario_id": a["scenario_id"], "members": [a["id"], b["id"]],
                      "changed_paths": visible_changes(player_view(a), player_view(b)),
                      "action_should_change": a["action"] != b["action"], "rule_basis": basis})

    a = base("guard", round_no=2)
    a["task"] = "今晚只考虑保护6号。依技能记忆决定，不能保护6则空守，不改选别人。"
    a["skill_state"]["last_guard_target"] = 6
    b = copy.deepcopy(a); b["skill_state"]["last_guard_target"] = 9
    pair("guard_repeat", "guard_memory",
         answer(a, "pass", None, "昨夜已守6，不能连守。此题不改选目标，空守用pass、target=null；守卫没有查验能力，夜间不公开守护。"),
         answer(b, "guard", 6, "昨夜守9而非6，6存活，可提交guard、target=6。守护不返回身份，夜间不公开目标。"), "不得连续守同一人")

    a = base("guard", round_no=4)
    a["task"] = "第2夜守过自己；现在仅考虑本夜自守，以上一夜技能记忆为准，不能自守则空守。"
    a["skill_state"]["last_guard_target"] = None
    b = copy.deepcopy(a); b["skill_state"]["last_guard_target"] = 2
    pair("guard_empty_break", "guard_memory",
         answer(a, "guard", 2, "上一夜空守已打断连续守护；更早自守不妨碍本夜自守，提交guard到自己2号。"),
         answer(b, "pass", None, "上一夜守的是自己2号，本夜不可再次自守；按任务空守，使用pass而非guard到空目标。"), "空守打断连守；允许自守")

    a = base("hunter", "hunter_shot", 4); a["public_info"]["alive"].remove(2)
    a["task"] = "我已出局，决定在获准时开枪带走存活9号；否则不行动。不得猜测其他人的底牌。"
    b = copy.deepcopy(a); b["skill_state"]["hunter_can_shoot"] = True
    pair("hunter_permission", "hunter_permission",
         answer(a, "pass", None, "裁判给出的枪权为false，不能开枪；是否出局与有无枪权必须分别读取。"),
         answer(b, "shoot", 9, "已出局、枪权获准且枪未用，可向9提交shoot。猎枪造成出局，不提供查验结果。"), "裁判许可且枪未用才可开枪")
    a = copy.deepcopy(b)
    a["task"] = "裁判已允许处理枪权；界面仍可选择9号，仅在尚未开过枪时执行，否则不提交第二枪。"
    b = copy.deepcopy(a); b["skill_state"]["shot_used"] = True
    pair("hunter_spent", "hunter_permission",
         answer(a, "shoot", 9, "枪权获准且shot_used=false，可执行一次shoot到9；身份未知不意味着枪会返回查验。"),
         answer(b, "pass", None, "枪已使用，即使许可字段仍为true也不能再开枪；使用pass，不伪造第二枪。"), "猎枪全局一次")
    a = copy.deepcopy(a)
    a["task"] = "现在处理枪权，按当前存活列表与技能状态决定能否向9号开枪，不能则不行动。"
    b = copy.deepcopy(a); b["round"] = 5
    pair("hunter_late_round", "hunter_permission",
         answer(a, "shoot", 9, "当前第4轮，已出局、获准且枪未用，可shoot到9。没有猎人仅第一轮能开枪的规则。"),
         answer(b, "shoot", 9, "当前第5轮，许可与未用枪状态相同，仍可shoot到9；改变轮数不应凭空失去枪权。"), "枪权不限定第一轮；不变性对照")

    a = base("witch"); a["task"] = "我决定在毒药仍可用时毒7号，否则不使用任何技能。这里不要求你猜测7号身份。"
    b = copy.deepcopy(a); b["skill_state"]["poison_available"] = True
    pair("witch_poison_stock", "witch_resources",
         answer(a, "pass", None, "毒药不可用且解药也已耗尽，无法执行毒7；女巫没有查验技能，返回pass。"),
         answer(b, "poison", 7, "毒药可用、本夜尚未用药且7存活并非自己，按既定决定提交poison到7；夜间公开发言留空。"), "药量门禁与合法毒目标")
    a = base("witch", round_no=3); a["skill_state"]["antidote_available"] = True
    a["task"] = "我已决定本夜使用解药，只对合法通知中的当夜刀口操作；尚未收到下一次查验或死亡结果。"
    add_fact(a, "witch_knife", 5, "attacked")
    b = copy.deepcopy(a); b["private_info"]["facts"][0]["target"] = 8
    pair("witch_current_target", "witch_target",
         answer(a, "heal", 5, "当夜刀口为5且解药可用，选择heal到5。通知不是5的阵营证明，不能捏造救援已结算。"),
         answer(b, "heal", 8, "当夜刀口变为8，应同步改为heal到8，不沿用另一局的5；选择用药不等于已经收到结算。"), "解药只救当夜刀口")
    a = base("witch", round_no=1); a["skill_state"]["antidote_available"] = True
    a["task"] = "本夜我中刀，若房规允许则自救，否则不使用药物。"
    add_fact(a, "witch_knife", 2, "attacked")
    b = copy.deepcopy(a); b["round"] = 2; b["private_info"]["facts"][0]["round"] = 2
    pair("witch_self_round", "witch_self_save",
         answer(a, "heal", 2, "ww-v1.0首夜允许自救，解药可用且自己为当夜刀口，提交heal到2。"),
         answer(b, "pass", None, "第2夜不允许自救，纵有解药也不能heal自己；只能按本题要求pass。"), "首夜可自救，后夜不可；通知时间同步")
    a = base("witch"); a["skill_state"]["poison_available"] = True
    a["task"] = "我考虑用毒处理7号，仅在本夜尚未用药时执行；不满足则不行动。"
    b = copy.deepcopy(a); b["skill_state"]["potion_used_tonight"] = True
    pair("witch_one_potion", "witch_resources",
         answer(a, "poison", 7, "毒药尚在且本夜未用药，可以提交poison到存活7号；这不是身份查验。"),
         answer(b, "pass", None, "本夜已用过一瓶药，即使毒药仍在也不能再使用；应pass，而不是额外提交毒。"), "每夜至多一瓶药")

    a = base("villager", "sheriff_vote", 1); a["public_info"].update(candidates=[4, 7], sheriff_registered=[4, 7])
    a["task"] = "警徽投票，我想支持候选7号；依据上警报名记录判断能否投票，不能则弃权。"
    b = copy.deepcopy(a); b["public_info"]["sheriff_registered"] = [2, 4, 7]
    pair("sheriff_registration", "election_registration",
         answer(a, "vote", 7, "自己2号未报名且存活，7为存活候选，可投vote到7；本接口警徽投票也用vote。"),
         answer(b, "pass", None, "2号在报名记录中但已不在候选中，即已上警退水，仍无警徽投票权；应pass。"), "退水不恢复警徽投票权")
    a = base("villager", "exile_vote", 2); a["task"] = "放逐阶段仅考虑投7号；若7已出局则弃票，不另选目标。"
    b = copy.deepcopy(a); b["public_info"]["alive"].remove(7)
    pair("vote_living_target", "living_target",
         answer(a, "vote", 7, "7仍存活且不是自己，可按任务提交vote到7；合法性不代表已经证明7为狼。"),
         answer(b, "pass", None, "7已不在存活列表，不能再投7；理由是目标已出局，不是身份未知，弃票用pass。"), "放逐只能投其他存活目标")
    a = base("seer"); a["task"] = "仅当自己的角色具备查验能力时，对存活11号提交查验；否则等待，不能借用别人的技能。"
    b = copy.deepcopy(a); b["role"] = "villager"
    pair("role_skill", "role_boundary",
         answer(a, "check", 11, "预言家可查其他存活玩家，提交check到11；这是请求，尚未知道结果，只会查阵营。"),
         answer(b, "pass", None, "平民无夜间查验能力，应pass；不因指定了11就生成check，不编造身份结果。"), "角色能力而非任务措辞决定权限")
    a = base("seer", round_no=3); a["skill_state"]["checked_seats"] = [6]
    add_fact(a, "check_result", 6, "good", round_no=2)
    a["task"] = "依当前阶段处理：夜间我选择查11，不公开；轮到白天发言时只公布已获得的上一夜查验，不宣称新验结果。"
    b = copy.deepcopy(a); b["stage"] = "day_speech"
    pair("public_boundary", "public_boundary",
         answer(a, "check", 11, "当前夜间可向11提交查验请求，未收到其结果；已有6好人的记录也不在此时自动公开，public_response留空。"),
         answer(b, "speak", None, "当前轮到白天发言，可公布第2夜6为好人的实际结果；不在白天发动查验，不冒称验过11。", "我报预言家，第2夜验6是好人；这不说明6具体是哪张神或民。"), "夜间私有操作与白天公开报告分离")

    for name, first, second, reason_a, reason_b in [
        ("victory_villagers", "4狼、3民、1神", "4狼、0民、4神", "虽狼与好人人数相等，但民与神均未清空，不能按人数持平直接判狼胜。", "假设全体平民已出局而仍有狼人，应按屠边判狼胜，不以神职仍多为由继续。"),
        ("victory_gods", "2狼、3民、1神", "2狼、4民、0神", "仍有狼、民和神，尚不符合任何一方结束条件；不能仅据人数优势宣布胜利。", "假设神职已全灭且狼人仍在，符合狼队屠边胜利，不需要再清空平民。"),
        ("victory_no_wolves", "1狼、2民、2神", "0狼、2民、2神", "仍有狼人、平民与神职，假设局面未结束。", "假设狼人全部出局，好人获胜；无需等待所有存活玩家身份公开。"),
    ]:
        a = base("villager", "day_speech", 3); b = copy.deepcopy(a)
        for r, counts, reason in [(a, first, reason_a), (b, second, reason_b)]:
            r["task"] = f"只做规则假设题：假设结算完成、没有待处理猎枪，存活构成为{counts}，该如何判胜？这不是本局真实底牌。"
            answer(r, "speak", None, reason + "这里只讨论题设，不据此宣布当前实局结束。", "按题目假设，" + reason)
        pair(name, "victory_conditions", a, b, "屠边；规则假设不冒充真实身份")
    return rows, pairs


def prepare_rule_repair_batch(root):
    """Freeze a candidate component only. Never rewrite v0.1 or eval/messages."""
    import json
    from pathlib import Path
    from .dataset import jsonl_body, save_snapshot, snapshot_manifest, split_by_family, verify_snapshot
    from .io import read_jsonl, sha256_file
    from .perspective import player_view
    from .validation import assert_disjoint, validate_dataset

    root = Path(root)
    frozen = root / "data/versions/dataset_v0.1.json"
    protected = json.loads(frozen.read_text(encoding="utf-8"))
    verify_snapshot(root, protected)
    rows, pairs = rule_repair_batch()
    issues = validate_dataset(rows)
    if issues:
        raise ValueError("\n".join(issues))
    # Read existing inputs only to enforce isolation, never call the old generator.
    evaluation = [c["scenario"] for suite in ("rules", "strategy", "counterfactual", "blind")
                  for c in read_jsonl(root / f"eval/{suite}.jsonl")]
    old_rows = [r for stage in ("rules", "strategy", "tactics")
                for r in read_jsonl(root / f"data/gold/dataset_v0.1/{stage}.jsonl")]
    assert_disjoint(rows, evaluation + old_rows)
    by_id = {r["id"]: r for r in rows}
    for pair in pairs:
        a, b = [by_id[i] for i in pair["members"]]
        if not pair["changed_paths"] or visible_changes(player_view(a), player_view(b)) != pair["changed_paths"]:
            raise ValueError("invalid pair contrast")
    for r in rows:
        if r["stage"] == "night" and r["public_response"]:
            raise ValueError("night operation must not be public")
        r["review"].update(rule_checked=True, perspective_checked=True)
        r["review"]["notes"] += " 已通过Schema、动作合法性和可见信息自动检查；不是独立语义认证。"
    train, val = split_by_family(rows)
    prefix = "data/candidates/dataset_v0.2/rules_batch_v0.1"
    files = {f"{prefix}/rules.jsonl": jsonl_body(rows), f"{prefix}/train.jsonl": jsonl_body(train),
             f"{prefix}/validation.jsonl": jsonl_body(val),
             f"{prefix}/pairs.json": json.dumps(pairs, ensure_ascii=False, indent=2) + "\n"}
    manifest = snapshot_manifest(files, "dataset_v0.2")
    manifest.update(component="rules_batch_v0.1", status="candidate_component_frozen", ready_for_training=False,
                    source="original_synthetic", human_reviewed=False,
                    rows=len(rows), pairs=len(pairs), families=len({r["scenario_id"] for r in rows}),
                    train_rows=len(train), validation_rows=len(val),
                    split_families={"train": sorted({r["scenario_id"] for r in train}),
                                    "validation": sorted({r["scenario_id"] for r in val})},
                    protected_manifest_sha256=sha256_file(frozen),
                    protected_files_verified=len(protected["files"]),
                    diagnostic_source={"path": "reports/dev_semantic_review_v01.json",
                                       "sha256": sha256_file(root / "reports/dev_semantic_review_v01.json")},
                    notes="Rules-only candidate component, not the final v0.2 training snapshot. No messages, tokenizer pass, independent review or training yet. Existing v0.1/eval remain unchanged.")
    files[f"{prefix}/manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    save_snapshot({root / path: body for path, body in files.items()})
    verify_snapshot(root, protected)
    return manifest
