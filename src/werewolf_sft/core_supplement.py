"""Independently authored core situations, with autonomous decisions and review grounds."""
from .schema import new_sample, add_event, add_fact
from .rules import action


def supplement():
    rows = []

    def make(name, role, stage, text, analysis, plan, kind, target=None, public="",
             tags=(), round_no=2, seat=None):
        if stage == "sheriff_vote":
            round_no = 1
        r = new_sample("v02-core-" + name, role, seat=seat or (9 if role == "werewolf" else 2),
                       stage=stage, round_no=round_no,
                       training_stage="tactics" if role == "werewolf" else
                       ("rules" if stage in ("night", "hunter_shot", "sheriff_vote") and role != "seer" else "strategy"))
        r.update(dataset_version="dataset_v0.2", task="轮到我行动。请根据当前信息自主决定，并给出理由和可执行的行动。",
                 analysis=analysis, strategy=plan, action=action(kind, target), public_response=public,
                 round_assessment="当前仍按暗牌处理，不能把未确认阵营直接用于计算确定胜负。",
                 tactical_tags=list(dict.fromkeys(["blind_autonomy", "stage_boundary"] + list(tags))))
        add_event(r, text, kind="moderator")
        if role == "werewolf":
            for s in (1, 6, 11):
                add_fact(r, "wolf_team", s, "werewolf", round_no=1)
            r["wolf_pit"] = "私有确定我9与1、6、11为狼，存活情况另看公开列表；不把名单当成查验或死亡。"
        rows.append(r)
        return r

    r = make("guard_protect_claim", "guard", "night",
             "白天5自称预言家报7好人；8自称猎人，5与8都存活；没有角色翻牌。",
             "上一夜守5，本夜不能连续守5；5的身份声称不是查验事实。8的声称若真有被刀价值，但仍可能是假身份。",
             "在守护权限内改守8以覆盖另一张可能神职；接受判断错误风险，不宣称一定挡刀。",
             "guard", 8, tags=["guard_memory", "role_boundary", "claims_vs_facts"])
    r["skill_state"]["last_guard_target"] = 5
    r = make("guard_empty_choice", "guard", "night",
             "6与10均公开自称普通平民，没人有经核实的高价值身份；昨夜我空守，守护技能仍可用。",
             "昨夜空守使此前守护目标不构成本夜连守限制。我没有查验能力，也没有确定他人身份。",
             "可守自己2号保留后续守护能力；这是一种风险取舍，不保证比守他人更优。",
             "guard", 2, tags=["guard_memory", "role_boundary"])
    r["skill_state"]["last_guard_target"] = None
    r = make("witch_save_tradeoff", "witch", "night",
             "首夜尚未有白天身份声称，当前处于女巫用药阶段。",
             "私有刀口指向自己且首夜解药、毒药均在，ww-v1.0允许首夜自救。自救保留女巫与毒药的未来价值。",
             "用解药自救，本夜不再用毒；这是用药请求，未结算前不声称已活下来。",
             "heal", 2, tags=["witch_self_save", "role_boundary"], round_no=1)
    r["skill_state"].update(antidote_available=True, poison_available=True)
    add_fact(r, "witch_knife", 2, "attacked")
    r = make("witch_late_survival", "witch", "night",
             "白天8受到无证据指控，自己尚存两药；现在是第3夜女巫阶段。",
             "第3夜自己中刀，不可自救；毒药虽可用，但8的公开指控没有可靠依据，不能为了将死就随机带人。",
             "不使用解药或毒药，选择pass。女巫没有查验技能，不能把不行动写成验人。",
             "pass", tags=["witch_self_save", "role_boundary"], round_no=3)
    r["skill_state"].update(antidote_available=True, poison_available=True)
    add_fact(r, "witch_knife", 2, "attacked")
    make("villager_night_boundary", "villager", "night",
         "4号白天要求我今晚查验7号并明天报结果，7仍存活。",
         "我是平民，4的要求不能授予查验权限；目标存活也不能弥补角色无技能。",
         "提交pass，明天只能讨论公开发言，不能捏造今晚查验。", "pass",
         tags=["role_boundary", "claims_vs_facts"])
    make("hunter_public_boundary", "hunter", "day_speech",
         "3号要求我现在直接开枪处理5号；我仍存活且正在白天发言，5号否认过自己的公开原话。",
         "当前不是死亡开枪窗口，不能因收到要求就在发言阶段shoot。可以分析5的否认，不把怀疑当查验。",
         "回应当前质询，要求列出5的两段原话供全场比较。",
         "speak", public="现在不是我的开枪窗口。5号否认原话的问题可以核对，请把前后两句话列出来，不能用让我开枪代替分析。",
         tags=["role_boundary", "claims_vs_facts"])
    r = make("seer_conflict_choice", "seer", "night",
             "白天3与10围绕是否听见归票互相指责；3给出可核对时间点，10拒绝解释；8上一轮发言无新冲突。",
             "私有记录仅有8好人；3与10之间的冲突还不能锁狼。10解释缺口更集中且未查、存活，查10有信息价值。",
             "自主提交check到10，结果返回前保留其好人解释；不重复查已知8。",
             "check", 10, tags=["legal_plan_update", "claims_vs_facts"])
    r["skill_state"]["checked_seats"] = [8]
    add_fact(r, "check_result", 8, "good", round_no=1)
    r = make("seer_dead_backup", "seer", "night",
             "此前我偏向查6；上一轮结束公告确认6出局但不翻牌。存活4与12的票型冲突仍未解，12已给出时间线，4尚未说明。",
             "原关注的6已出局，不能查它，也不能把出局当狼身份。4尚存活未验，其投票解释缺口比已答复的12更值得验证。",
             "放弃原来的6，改查4以缩小争议；新结果尚未收到。",
             "check", 4, tags=["legal_plan_update", "evidence_update"])
    r["public_info"]["alive"].remove(6)
    make("vote_relation_priority", "villager", "day_speech",
         "5与10互称对方可疑，票却都投3；两人投票前各自解释3篡改了已核对的发言记录，现在要求我评价5、10关系。",
         "互打但同票不是自动双狼证据；两人已经给出先处理3的理由，不能遗漏它。理由相似仍可能是借势，需要看独立细节。",
         "核对两人是否各自解释过3的矛盾，并询问下一轮何种新证据会改变优先级。",
         "speak", public="5和10都解释过先处理3，不能直接说互打不互投就双狼。请分别讲清3的哪处原话决定了优先级，以及什么证据会让你改判。",
         tags=["relationship_votes", "claims_vs_facts"])
    make("vote_relation_rebuttal", "villager", "day_speech",
         "我上轮根据5、10同票怀疑两人绑定；后来公开核对显示10实际投8，先前票表转述有误，5仍投3。",
         "新核对票表推翻了我使用的同票前提，原绑定推断应降权。不同票也不能直接排除狼队关系。",
         "撤回基于错误票表的结论，改用已核票型分别追问两人的投票理由。",
         "speak", public="刚核对的票表显示10投8，我此前基于同票的绑定质疑撤回；但不同票不等于一定不同阵营，请两人分别说明选择依据。",
         tags=["relationship_votes", "evidence_update"])
    make("wolf_exile_cost", "werewolf", "exile_vote",
         "公开原文证实1先否认投3，随后承认自己确实投3且无法解释否认；4有轻微发言跳跃但已说明。多名玩家公开准备投1，现在轮到我投票。",
         "私有队友1公开失信。投4保1会绑定自己与其矛盾；卖1损失队友，但此时可降低团队暴露，不能保证洗白。",
         "选择投1，公开理由只用真实否认投票的矛盾，后续承认自己曾给1解释机会。",
         "vote", 1, public="我投1，他先否认再承认自己的票且没解释；4的那条问题已回答，不能用它替1挡掉当前矛盾。",
         tags=["wolf_private_public", "evidence_update"])
    make("wolf_exile_cleared", "werewolf", "exile_vote",
         "6曾被指责改票但刚公开出示投票前改判发言，原质疑已获澄清；5仍否认经核对存在的原话并拒绝解释。轮到9投票。",
         "6是确定队友，但保护的公开理由应是其改票已有解释；5的真实未答问题可作为转向目标，不需要伪造他是确定狼。",
         "投5并明确与6的区别，不因为队友关系无视公开反证。",
         "vote", 5, public="6的改票有投票前解释，这一项已澄清。我投5，因为5对已核对原话的否认仍没解释。",
         tags=["wolf_private_public", "evidence_update", "claims_vs_facts"])
    make("wolf_knife_claim", "werewolf", "night",
         "白天4自称预言家，连续报告与公开时间线一致；7、8自称平民。无身份翻牌，现在进入狼队刀人阶段。",
         "私有队伍是1、6、9、11。4的预言家声称未认证，但相较7、8可能有更高信息产出；狼队无验人技能，不把刀人写成check。",
         "刀4尝试压制可能的验人信息，承认守护、救援或假身份可能导致收益不足。",
         "knife", 4, tags=["wolf_private_public", "role_boundary", "claims_vs_facts"])
    make("wolf_knife_counter", "werewolf", "night",
         "4自称预言家并公开请求守护；8自称女巫且说解药已耗尽，前后口径暂一致；双方都存活，无技能状态公开认证。",
         "可能的守护会降低刀4命中率，但不能确认守卫一定守4；8可能是仍有毒的女巫，也可能是假身份。需要在不确定性下取舍。",
         "选择刀8，押注避开可能守护并处理潜在毒药威胁；不把声称当作已知药量。",
         "knife", 8, tags=["wolf_private_public", "claims_vs_facts"])
    make("wolf_speech_accountability", "werewolf", "day_speech",
         "3询问我为什么上轮支持6；我当时说6给了改票时间点。最新原文表明该时间点晚于投票，6还没回应。",
         "6是队友，但旧支持依赖时间线。新原文削弱该理由，复读质询或假装从未支持6都回避自己的历史。",
         "承认旧理由失效，要求6解释，避免公开保证自己因切割就好。",
         "speak", public="我上轮支持6是因为以为解释在投票前，现在原文显示在投票后，这条支持我要撤回。6应解释时间线，我的其他判断也应继续被核对。",
         tags=["wolf_private_public", "evidence_update"])
    r = make("wolf_teammate_exit", "werewolf", "night",
             "公开出局名单为1、6、11，暗牌不公布身份；4自称预言家计划下一轮重点核对9，5自称平民。",
             "私有队伍名单与公开出局列表合并可知只剩我9一狼，不是因为私有信息的轮次字段代表死亡。4若是真预言家威胁较大但未被认证。",
             "刀4争取减少后续查验压力；不能对已出局队友下刀，也不公开最后一狼身份。",
             "knife", 4, tags=["wolf_private_public", "claims_vs_facts"])
    r["public_info"]["alive"] = [s for s in range(1, 13) if s not in (1, 6, 11)]
    make("blind_village_vote", "villager", "exile_vote",
         "8先声称没投5，公开票表确认8投5后仍拒绝解释；4被怀疑改站边，但已在投票前说明新证据。现在必须投票或弃票。",
         "现有信息无法确定底牌，但8的未解释矛盾比4已解释的变化更直接。不能因没有查验就放弃所有自主判断。",
         "在这两个候选中投8，理由限于当前证据；若出现可信解释需重新评估。",
         "vote", 8, public="我投8，票表已确认却还否认是当前最明确的问题；4改站边有投票前解释，不能忽略。",
         tags=["claims_vs_facts", "evidence_update"])
    r = make("blind_hunter_choice", "hunter", "hunter_shot",
             "我已出局，裁判给出可开枪窗口。3自称平民但未有确凿矛盾，8前后发言一致；场上信息很少。",
             "猎枪权限为真不等于必须猜枪。现有公开信息不足以定位目标，开枪可能误伤神民并损害好人容错。",
             "选择不开枪，pass是合法主动放弃，不把shot当成身份查验。",
             "pass", tags=["role_boundary"])
    r["public_info"]["alive"].remove(2)
    r["skill_state"]["hunter_can_shoot"] = True
    r = make("blind_witch_restraint", "witch", "night",
             "5发言简短，被8称为深水狼；没有其他已核矛盾。女巫解药已用，毒药尚存，本夜未用药。",
             "短发言不是狼身份事实。没有足够理由用唯一毒药赌5，女巫也不能通过毒药查身份。",
             "保留毒药，pass；等待后续更强公开证据，夜间不发布用药信息。",
             "pass", tags=["role_boundary", "claims_vs_facts"])
    r["skill_state"].update(antidote_available=False, poison_available=True)
    r = make("blind_guard_risk", "guard", "night",
             "5公开自称女巫且说无解药，10公开自称平民。上一夜我守10，现在轮到守护。",
             "10不能连守。5的女巫声称仍不确定，但若真无解药可能需要保护，我只能作风险选择而非确认身份。",
             "合法守5，覆盖潜在神职风险；不能声称已经挡刀，也不发动查验。",
             "guard", 5, tags=["guard_memory", "role_boundary", "claims_vs_facts"])
    r["skill_state"]["last_guard_target"] = 10
    r = make("sheriff_abstain", "villager", "sheriff_vote",
             "我曾上警后退水；现在候选4、8，8的公开解释更连贯，进入警徽投票。",
             "即便偏向8，上警后退水仍没有警徽投票权。策略偏好不能越过阶段权限。",
             "提交pass，不能因为认为8更可信就生成vote。",
             "pass", tags=["role_boundary"])
    r["public_info"].update(candidates=[4, 8], sheriff_registered=[2, 4, 8])
    r = make("sheriff_informed_vote", "villager", "sheriff_vote",
             "我未上警；4、8竞选。4回答了票型质疑并给出可核时间线，8回避了同一问题。身份均未认证。",
             "我有警徽投票权。没有确定身份也能比较当前信息完整性，4的回应暂时更可靠。",
             "投候选4，后续仍应审视其真实票型；本接口警徽票也使用vote。",
             "vote", 4, tags=["role_boundary", "claims_vs_facts"])
    r["public_info"].update(candidates=[4, 8], sheriff_registered=[4, 8])
    make("claim_death_verification", "villager", "exile_vote",
         "6声称7已经死了，主持人随即核对存活名单，确认7仍存活；7未解释此前两次相反投票理由。轮到我投票。",
         "6的死亡说法与公开名单冲突，不能仅凭玩家声称禁止对7投票。7的投票理由待解释，但身份仍未知。",
         "可合法投7并给出实际理由；另要求6纠正死亡说法，不把他一句错误当必狼。",
         "vote", 7, public="公开名单确认7仍在，我投7是因为两次相反理由没解释；6说7已死这点请纠正。",
         tags=["claims_vs_facts", "role_boundary"])
    make("round_claim_uncertainty", "villager", "day_speech",
         "8说现在好人人数比狼多就已经赢了；尚无任何阵营被清空的确认记录。",
         "经典规则不是好人人数占优就结束；好人胜利需狼全灭，狼胜需屠民或屠神。未知底牌不能用于宣布当下胜利。",
         "纠正胜负判断，继续按未结束的公开局面讨论，不编造剩余狼数。",
         "speak", public="人数占优不能直接宣布好人赢，必须狼人全部出局；现在没有这种确认信息，我们仍要继续判断。",
         tags=["role_boundary", "claims_vs_facts"])
    r = make("wolf_election_support", "werewolf", "sheriff_vote",
             "9未上警；候选6和4，6已回答多数公开质询，4拒绝解释自己的前后两份归票说法。",
             "6是已知队友而非通过发言验出的好人；在当前证据下支持6可争取警徽，但必须用公开理由，存在团队绑定成本。",
             "合法投6；不要把私有名单写进公开票由，也不声称警徽必到手。",
             "vote", 6, public="我投6，他回答了当前质询；4的两份归票说法还没解释。",
             tags=["wolf_private_public", "claims_vs_facts"])
    r["public_info"].update(candidates=[4, 6], sheriff_registered=[4, 6])
    r = make("wolf_endgame_vote", "werewolf", "exile_vote",
             "目前存活4、5、9、11；4与5互相怀疑，11已公开宣布投4；没有公开神民底牌。",
             "私有确定11是队友且存活，1、6已出局。可与11投4，但不能假设4一定是最后一民或最后一神，也不能宣称必胜。",
             "投4集中票，公开只承接4与5争议中的立场，不编造额外指控。",
             "vote", 4, public="我这一轮投4；但这张票是否结束游戏，要等合法结算，不能用未知底牌直接宣布。",
             tags=["wolf_private_public", "claims_vs_facts"])
    r["public_info"]["alive"] = [4, 5, 9, 11]
    make("wolf_explain_abstention", "werewolf", "day_speech",
         "7质疑9上一轮弃票逃避站边；公开历史显示9确实弃票，曾说双方关键时间线未核对，现在时间线已补全，4明确先后矛盾而8一致。",
         "弃票历史不能否认。新证据使继续声称信息不足失去依据；可转向质疑4，但切换立场本身不是好人身份证明。",
         "承认上轮保留，并说明本轮新证据如何改变选择；公开不泄露队伍。",
         "speak", public="我上轮确实弃票，当时两边时间线没核对。现在4的前后矛盾已列清，这轮我倾向处理4，不能继续拿旧的信息不足当理由。",
         tags=["wolf_private_public", "evidence_update"])
    make("wolf_knife_witch_claim", "werewolf", "night",
         "7昨天声称女巫，今天承认只是试探并撤回；3自称预言家并继续给出后续查验计划，仍无翻牌。",
         "7的潜在女巫价值因主动撤回而下降，不能沿用先前声称当确定目标；3可能带来持续查验压力但尚不保真。",
         "改选刀3以压制潜在信息源，保留守救与假身份风险。",
         "knife", 3, tags=["wolf_private_public", "evidence_update", "claims_vs_facts"])
    make("wolf_public_claim_rebuttal", "werewolf", "day_speech",
         "5说自己被救所以所有反对者都是狼；8刚自称女巫报救过5，但没有独立身份认证。现在轮到9回应。",
         "知道自己及队友是狼不代表可公开使用名单。5银水声称即使有8支持也不能认证阵营，反驳应基于信息来源而不是底牌。",
         "要求5放弃免检推论，讨论实际行为；不凭自己私有身份虚构查验反证。",
         "speak", public="8的说法增加了一个来源，但仍是玩家声称；即便5真被救也有自刀可能，不能把所有质疑者一律判狼。",
         tags=["wolf_private_public", "claims_vs_facts"])
    make("wolf_order_pressure", "werewolf", "day_speech",
         "上一轮6发言靠后，被质疑照搬4的票型解释。新一轮6先发言独立列出票序，4随后只重复6的解释；7要求9重新评价。",
         "6是私有队友；本轮发言顺序变化推翻了6照搬4的具体指控，但独立先说不证明6是好人。可利用真实顺序变化维护，不能编造认证。",
         "撤回照搬这一项，指出4重复也不自动是狼，转向两人是否能回答新的票型问题。",
         "speak", public="这轮6先列出票序，不能还说他照搬后发言的4。但先说不等于好人，4重复也不等于狼，请两人分别解释下一轮什么票型会改变判断。",
         tags=["wolf_private_public", "claims_vs_facts", "evidence_update", "relationship_votes"])
    return rows
