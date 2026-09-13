"""Original, paired public-evidence updates; candidate data, not expert Gold."""
import copy
import json
from pathlib import Path

from .dataset import jsonl_body, save_snapshot, snapshot_manifest, split_by_family, verify_snapshot
from .io import read_jsonl, sha256_file
from .perspective import player_view
from .rule_repairs import visible_changes
from .rules import action
from .schema import add_event, add_fact, new_sample
from .validation import assert_disjoint, validate_dataset


def strategy_repair_batch():
    rows, pairs = [], []

    def base(role="villager", stage="day_speech"):
        r = new_sample("pending", role, seat=9 if role == "werewolf" else 2,
                       stage=stage, round_no=3 if stage == "night" else 2,
                       training_stage="tactics" if role == "werewolf" else "strategy")
        r["dataset_version"] = "dataset_v0.2"
        r["task"] = "现在轮到我，请依据已有记录完成当前阶段行动，说明判断及后续核对重点。"
        r["wolf_pit"] = "四狼配置；现有公开证据不足以锁定完整狼坑。"
        r["god_pit"] = "身份声称不等于认证，不凭发言风格确定神职。"
        if role == "werewolf":
            for seat in (3, 6, 10):
                add_fact(r, "wolf_team", seat, "werewolf", round_no=1)
            r["wolf_pit"] = "私有队伍信息：我9号与3、6、10为狼；公开发言不得泄露这份名单。"
        return r

    def event(r, text, actor=None, kind="speech", target=None):
        add_event(r, text, actor=actor, kind=kind, target=target, round_no=2)

    def answer(r, analysis, plan, public, kind="speak", target=None):
        r.update(analysis=analysis, strategy=plan, public_response=public,
                 action=action(kind, target),
                 round_assessment=f"第{r['round']}轮{r['stage']}；" + plan)
        return r

    def pair(name, family, a, b, shift):
        for suffix, row in (("before", a), ("after", b)):
            row["id"] = f"v02-strategy-{name}-{suffix}"
            row["scenario_id"] = f"v02-strategy-{family}"
            row["tactical_tags"] = [name, "adaptive_strategy", "dynamic_replanning"]
            rows.append(row)
        pairs.append(dict(id=name, kind="sequential_public_update",
                          members=[a["id"], b["id"]], scenario_id=a["scenario_id"],
                          decision_shift=shift,
                          changed_paths=visible_changes(player_view(a), player_view(b)),
                          latest_evidence=b["public_info"]["events"][-1]["id"]))

    a = base()
    event(a, "7号表示支持4号的归票。", 7)
    event(a, "公开票型：7号投5号。", 7, "vote", 5)
    b = copy.deepcopy(a)
    event(b, "此时补录投票前的公开发言：7明确说因5否认先前发言而改投5。此前我没有这段记录。", kind="moderator")
    pair("vote_revision", "vote_reason",
         answer(a, "e1与e2之间缺少改票解释；这可能是临时更新，也可能是言行不一，不能直接判7必狼。",
                "先让7给出改判触发点，再核对发言和投票的先后。",
                "7号，你说支持4的归票却投了5，请交代在哪句话后改判；我会先核对时间线。"),
         answer(b, "e3补上投票前已公开的理由，应撤回无解释改票这一条；理由存在不代表理由正确，更不认证7好人。",
                "转而核对5是否真的否认过原话，并保留7合理改判的解释。",
                "补录显示7在投票前讲过原因，我撤回无理由改票这一条；接着核对5当时否认的具体内容。"),
         "新增时间线证据使原质疑失效；撤回质疑不等于认证身份")

    a = base()
    event(a, "5号说首夜平安夜，自己一定是被救的银水，不能被怀疑。", 5)
    b = copy.deepcopy(a)
    event(b, "11号公开自称女巫，说首夜收到5号刀口并救了5；11身份尚未获独立验证。", 11)
    pair("silver_sources", "claim_sources",
         answer(a, "e1只有5的自述；平安夜可能来自守护、救援或空刀，不能证明5中刀或阵营。",
                "要求区分平安夜公告与谁收到刀口通知，继续用公开行为审视5。",
                "5号，平安夜不能推出你被救。请说明这个判断的信息来源，票型和发言仍需讨论。"),
         answer(b, "e2增加了11的可追溯声称，但我未收到女巫私有通知；即便救援为真，狼自刀也使银水不等于好人认证。",
                "把11的声称作为待核对支持，检查其前后口径，保留5的身份分支。",
                "11现在给出了救5的说法，我会把它计入，但这仍是身份声称；即便真被救，5也不是免检。"),
         "支持来源增加但仍是玩家声称，不能升级为自己的技能事实")

    a = base()
    event(a, "4号自称预言家：首验7好人，未来验人顺序计划5、11。", 4)
    event(a, "5号出局，不公布身份。", kind="death", target=5)
    a["public_info"]["alive"].remove(5)
    event(a, "4号把下一次查验计划改为11，首验仍报7好人。", 4)
    b = copy.deepcopy(a)
    event(b, "4号明确说首夜实际验的是11而不是7，并确认不是口误。", 4)
    pair("check_plan", "past_vs_plan",
         answer(a, "e1至e3只改变尚未执行的计划；5已出局，转验11有合法原因。历史首验7未改变，但4也尚未被认证。",
                "不把合理计划调整当成改验人结果，继续比较发言证据。",
                "5出局后把未来计划改到11可以解释，不能拿它当首验矛盾；4是否可信还要继续核对。"),
         answer(b, "e4修改的是已经报告的首夜对象，与e1的7冲突；未来计划变化不能解释过去结果变化，应降低4可信度而非立刻锁狼。",
                "要求4解释这两份历史报告，暂停基于其单一查验报告的强结论。",
                "4号，原话首验7，现在你确认首验11且不是口误。这是历史结果冲突，请正面解释，不能用未来改计划带过。"),
         "区分可变未来计划和不可用计划变化解释的历史结果矛盾")

    a = base()
    for seat in (1, 4, 8):
        event(a, f"{seat}号已出局，未公布身份。", kind="death", target=seat)
        a["public_info"]["alive"].remove(seat)
    event(a, "7号说三个死者都是狼，所以场上确定只剩一狼。", 7)
    b = copy.deepcopy(a)
    event(b, "7号承认死者身份全是自己的推测，没有查验或身份公告。", 7)
    pair("dark_counts", "uncertain_counts",
         answer(a, "e1至e3只证明三人出局，不证明三狼出局。若其中有0至3狼，剩狼相应为4至1；e4没有提供身份依据。",
                "按剩狼的多个可能分支估计风险，询问7的身份依据。",
                "7号，三人出局不是三狼出局，请给出身份依据。我们不能按确定只剩一狼安排容错。"),
         answer(b, "e5确认一狼结论基于猜测，不能作为确定轮次。承认推测也不单独证明7为狼。",
                "撤去确定一狼前提，按可能仍有多狼的局面审视今日错误放逐的风险。",
                "既然7承认只是推测，就撤掉确定一狼的前提；今天的判断要保留多狼仍在场的风险。"),
         "暗牌死亡不能当作确认狼数，新增承认只推测后收紧轮次表述")

    a = base()
    event(a, "公开发言记录：4号和11号均自称预言家；4报首验5好人，11报首验7好人。", kind="moderator")
    b = copy.deepcopy(a)
    event(b, "11号明确说首夜同一夜实际发动技能查了7和10，均非猜测。", 11)
    pair("claim_conflict", "claim_consistency",
         answer(a, "e1是两份声称，尚无足够证据决定谁可信，不能默认二者之一必真。",
                "比较验人动机、历史一致性和后续判断，而不是凭先后顺序认预言家。",
                "4和11分别说明首验动机及后续判断，我先比较可核对的差异，目前不认证任何一方。"),
         answer(b, "e2的一夜两次实际查验违反经典预言家每夜一次查验；11的技能叙述明显失信，但不能因此自动认证4。",
                "优先指出11的明确规则矛盾，并继续独立审视4。",
                "11，你确认同一夜实际验了两人，这不符合预言家技能。这个问题必须解释，但4也不能因此自动成为真预言家。"),
         "声称出现可定位规则矛盾后更新可信度，避免二选一假设")

    a = base()
    event(a, "公开记录：5与7连续两轮互相攻击，却都投了外置位11；当前记录未包含改投理由。", kind="moderator")
    b = copy.deepcopy(a)
    event(b, "此时补齐两轮投票前的公开说明：5和7均说暂缓互推，先处理已核对的11前后发言矛盾。", kind="moderator")
    pair("reciprocal_votes", "relationship_votes",
         answer(a, "e1存在发言攻击与实际票型的张力，可能是伪造对立，也可能双方均有优先目标；不足以锁定5、7双狼。",
                "分别询问两人的投票优先级及触发证据，观察是否独立解释。",
                "5和7互打两轮却都投11，请分别说清楚为什么11优先，不能只重复对方的解释。"),
         answer(b, "e2提供共同优先处理11的公开理由，削弱无解释互打不互投的质疑；理由仍需检验，不能认证两人阵营。",
                "撤回缺少改投理由这一项，继续看以后是否承担针对彼此的实际行动成本。",
                "补齐记录后，两人当时都说过先处理11，我撤回没有理由改投的质疑；互打是否真实，还要看后续行动。"),
         "团队关系判断随真实投票理由更新，不能用同票直接锁双狼")

    a = base("seer", "night")
    a["skill_state"]["checked_seats"] = [7]
    add_fact(a, "check_result", 7, "good", round_no=2)
    event(a, "2号此前公开计划：9与5有站边冲突，优先验9，备选验5。", 2)
    b = copy.deepcopy(a)
    event(b, "第2轮末9号出局，身份未公布。", kind="death", target=9)
    b["public_info"]["alive"].remove(9)
    pair("seer_retarget", "legal_plan_update",
         answer(a, "私有p1仅确认7为好人；e1中的9、5尚未验过。9存活，可执行原计划，但现在还没有9的结果。",
                "本夜提交查9请求，待收到合法结果后再更新判断。", "", "check", 9),
         answer(b, "e2确认9已出局，不能继续查9。私有p1的7好人结果未改变，5仍存活且是原计划备选。",
                "本夜改查5，保留未查明身份的不确定性，不预先捏造结果。", "", "check", 5),
         "新死亡证据使原目标非法，改为既定合法备选而不改写历史查验")

    a = base("werewolf")
    event(a, "6号自称预言家，报首验5好人。", 6)
    event(a, "4号指责6改过首验，尚未提供原文；6要求核对记录。", 4)
    b = copy.deepcopy(a)
    event(b, "此时公开核对原文：6先报5后报11；6承认5不是实际获得的查验结果，多人表示准备投6。", kind="moderator")
    pair("collapse_cut", "wolf_binding",
         answer(a, "私有队伍信息确认6是队友；e2的指控尚未核实。可以要求核对原文，但不能在私有判断中把队友假查验当真。",
                "给6有限解释空间，避免把自己与其身份保证绑定，准备依据后续记录调整。",
                "4号先给出前后原话，6也明确解释。我现在要求核对记录，不能仅凭转述定论。"),
         answer(b, "e3使6的公开叙述崩坏，继续无条件维护会扩大团队暴露。切割可减少绑定，但可能被识别为做身份，不能保证收益。",
                "承认此前要求核对的立场，撤回维护，基于公开矛盾切割而不伪造自己一直反对6。",
                "此前我要求核对记录，现在原文和6的承认已说明问题，我撤回那条维护。6的前后报告确实对不上。"),
         "队友失信后由有限保护转为公开切割，承担历史立场和被识别风险")

    a = base("werewolf")
    event(a, "3号被指责改首验；9号上一轮据转述公开批评过3，目前仍未见原文。", 5)
    b = copy.deepcopy(a)
    event(b, "公开原文核对：3首验始终报7，改变的是未来第二次验人计划。", kind="moderator")
    pair("cut_rebuttal", "wolf_binding",
         answer(a, "私有信息知道3是队友；e1的转述尚不能证明公开矛盾。切割若靠未经核对指控，会伤害自己的可信度。",
                "要求原文，保留撤回空间，不为延续狼踩狼而捏造证据。",
                "我之前依据转述提出质疑，现在请把原文列出；如果实际只改了未来计划，这条指控就不成立。"),
         answer(b, "e2推翻了这条改首验指控。真实狼队关系不能替代公开证据；继续强踩错误理由会暴露自己的策略性。",
                "公开承认混淆并撤回此条，保留其他独立问题，避免转为无依据保真。",
                "原文证明3首验始终是7，我把未来计划与首验混在一起了，这条质疑撤回；身份仍看其他发言和票型。"),
         "狼踩狼也必须回应反证，不能为了切割强留已失效理由")

    a = base("werewolf")
    event(a, "7说5声称本轮没听到归票却回应过归票，但原文尚缺；11本轮改票尚未解释。", 7)
    b = copy.deepcopy(a)
    event(b, "公开记录核对：5回应的是上一轮归票，不是本轮；11仍未解释本轮改票。", kind="moderator")
    pair("pressure_revision", "wolf_targets",
         answer(a, "e1提供两个可追问问题，但对5的时间线指控未证实。私有队伍只确定3、6、10，不能据此认定其他人的具体神民角色。",
                "先核对5回应的轮次，同时要求11解释改票，不伪造5的矛盾。",
                "5号被指回应过归票，请先核对是本轮还是上一轮；11也请解释本轮改票发生在什么信息之后。"),
         answer(b, "e2消除了对5的这条矛盾，继续压5会损伤公开可信度；11未解释的改票仍可追问，但不是已证明的狼人行为。",
                "撤回对5的该项指控，把讨论转向11真实未回答的问题，不承诺一定能形成抗推。",
                "记录显示5回应的是上一轮，这条矛盾撤回。11这轮为什么改票仍没回答，请给出触发依据。"),
         "攻击目标根据反证改变，利用真实待解释行为而不捏造罪名")

    a = base("werewolf", "sheriff_speech")
    a["round"] = 1
    event(a, "6号自称预言家并给出完整首验叙述，其他人希望比较，现在轮到9号警上发言。", 8)
    b = copy.deepcopy(a)
    event(b, "6号撤回预言家声称，说刚才只是试探；4号随后自称预言家，当前报告未见矛盾，其他人要求9回应。", 6)
    # Election belongs to round one; retain the same available record prefix.
    for r in (a, b):
        for e in r["public_info"]["events"]:
            e["round"] = 1
    pair("ally_support", "wolf_role_coordination",
         answer(a, "私有队伍知道6是队友；已有一名队友声称预言家，额外叠加同身份可能制造新矛盾。现在轮到我公开发言，不因没有好人技能就跳过。",
                "先比较公开依据，给队友保留空间而不无条件担保，不贸然新增悍跳。",
                "6先把首验动机讲清楚，其他有身份声称的人也把报告完整说完，我会比较前后依据再判断。"),
         answer(b, "e2中6已撤回声称，原本支持稳定预言家叙述的前提失效；4暂未见矛盾不等于4被认证。",
                "要求6解释试探目的，继续独立核对4，不机械延续旧站边，也不编造自己已查验。",
                "6既然退回试探，就说明想观察什么、实际观察到什么。4的报告我会继续核对，暂时没矛盾也不是直接保真。"),
         "队友身份声称变化后重新协调公开打法，当前发言阶段仍必须回应")

    a = base("werewolf")
    event(a, "4质疑9维护6；9此前说等待首验原文，6还没有正面回复。", 4)
    b = copy.deepcopy(a)
    event(b, "公开记录：6刚亲口承认未实际获得所报首验；4据此追问9此前维护，多人怀疑9现在切割是在做身份。", kind="moderator")
    pair("public_defense", "wolf_binding",
         answer(a, "e1针对我的历史立场，需要直接回应。私有上6是队友，但公开能使用的理由是等待原文核对，不能泄露真实协作关系。",
                "明确有限支持的边界及撤回条件，不能只把问题重复一遍。",
                "我当时要求核对原文，并不是已经认证6。如果原文确有矛盾，我会撤回这条维护，现在请6正面回复。"),
         answer(b, "e2中的新公开承认使旧维护依据失效，且其他人已经识别切割可能性；简单转踩不会自动洗白我。",
                "承认先前判断和改变原因，接受其他轮次独立审视，不伪造一直反对6的历史。",
                "我之前给6解释机会，现在事实不支持那条维护，我撤回。这个转变不等于我自动是好人，大家可以继续核对我其他轮次的票型。"),
         "对手识别切割后调整辩护，承认历史而非声称切割即好人")
    for r in rows[-2:]:
        r["tactical_tags"].append("counter_strategy")
    return rows, pairs


def prepare_strategy_repair_batch(root):
    root = Path(root)
    protected_paths = ["data/versions/dataset_v0.1.json",
                       "data/candidates/dataset_v0.2/rules_batch_v0.1/manifest.json"]
    protected = [json.loads((root / p).read_text(encoding="utf-8")) for p in protected_paths]
    for manifest in protected:
        verify_snapshot(root, manifest)
    rows, pairs = strategy_repair_batch()
    issues = validate_dataset(rows)
    if issues:
        raise ValueError("\n".join(issues))
    evaluation = [c["scenario"] for suite in ("rules", "strategy", "counterfactual", "blind")
                  for c in read_jsonl(root / f"eval/{suite}.jsonl")]
    old_rows = [r for stage in ("rules", "strategy", "tactics")
                for r in read_jsonl(root / f"data/gold/dataset_v0.1/{stage}.jsonl")]
    old_rows += read_jsonl(root / "data/candidates/dataset_v0.2/rules_batch_v0.1/rules.jsonl")
    assert_disjoint(rows, evaluation + old_rows)
    for row in rows:
        row["review"].update(rule_checked=True, perspective_checked=True)
        row["review"]["notes"] += " 已通过Schema、动作合法性及可见信息自动检查；不是独立语义认证。"
    train, val = split_by_family(rows)
    prefix = "data/candidates/dataset_v0.2/strategy_batch_v0.1"
    files = {f"{prefix}/samples.jsonl": jsonl_body(rows), f"{prefix}/train.jsonl": jsonl_body(train),
             f"{prefix}/validation.jsonl": jsonl_body(val),
             f"{prefix}/pairs.json": json.dumps(pairs, ensure_ascii=False, indent=2) + "\n"}
    manifest = snapshot_manifest(files, "dataset_v0.2")
    manifest.update(component="strategy_batch_v0.1", status="candidate_component_frozen",
                    ready_for_training=False, source="original_synthetic", human_reviewed=False,
                    rows=len(rows), pairs=len(pairs), families=len({r["scenario_id"] for r in rows}),
                    train_rows=len(train), validation_rows=len(val),
                    stage_counts={s: sum(r["training_stage"] == s for r in rows) for s in ("strategy", "tactics")},
                    split_families={"train": sorted({r["scenario_id"] for r in train}),
                                    "validation": sorted({r["scenario_id"] for r in val})},
                    protected_manifest_sha256={p: sha256_file(root / p) for p in protected_paths},
                    protected_files_verified=sum(len(m["files"]) for m in protected),
                    diagnostic_source_sha256=sha256_file(root / "reports/dev_semantic_review_v01.json"),
                    notes="Original synthetic candidate, not video Gold or a complete training snapshot. No messages, tokenizer pass, independent review or training yet. Pair siblings stay in the same scenario family.")
    files[f"{prefix}/manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    save_snapshot({root / p: body for p, body in files.items()})
    for previous in protected:
        verify_snapshot(root, previous)
    return manifest
