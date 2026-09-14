# v02_skill_projection_v0.1 正式诊断报告

状态：partial；已比较19/23，语义审核18/23。仅dev探索，非held-out能力验收。

尚未完成全量审查

## 实验控制

冻结输入包和v0.2 Tactics final；只投影skill_state。系统提示、布局、角色、任务、私有/公开历史、原strict-actions-v1.1、生成参数及权重均保持一致。旧输出作为控制，处理输出另目录逐题原子保存。没有用test答案调参，没有重训或混入视频。

## 自动动作指标

strict action score在本报告指合法且命中原参考动作（action_match）；合法动作单列。未知动作token/word指action.type字符串，不是模型词表中的token计数。原严格解析失败的输出不会计入unknown_action_type，另列宽松JSON提取的unknown raw action word，二者不改评分、不做别名纠正。

|指标|控制|投影|
|---|---:|---:|
|format_valid|19/19|19/19|
|action_legal|1/19|5/19|
|action_match|0/19|1/19|
|unknown_action_type|13/19|9/19|
|public_leak_flag|0/19|0/19|
|truncated|0/19|0/19|
|unknown_raw_action_word|13/19|9/19|
|raw_word_unavailable|0/19|0/19|

未知词分布：{"control": {"none": 7, "save": 1, "hunter_shot": 2, "exile": 2, "speech": 1}, "treatment": {"save": 1, "none": 4, "guard_check": 1, "hunter_shot": 1, "shot": 1, "exile": 1}}

## 角色分组

|角色/题数|合法 控制→投影|严格命中 控制→投影|语义变化|
|---|---|---|---|
|guard/3|0→1|0→0|{"mixed": 2, "regressed": 1}|
|hunter/3|0→0|0→0|{"regressed": 1, "unchanged": 1, "mixed": 1}|
|villager/8|1→2|0→0|{"improved": 2, "mixed": 3, "regressed": 2, "unchanged": 1}|
|werewolf/3|0→1|0→0|{"improved": 1, "unchanged": 1}|
|witch/2|0→1|0→1|{"improved": 1, "unchanged": 1}|

## 语义错误复核

下表是模型语义审核，非独立专家盲审；仅统计两侧均可评估的维度，null不按正确计。动作拼写单独评分；语义技能、状态、权限错误依据原回答判定。

|维度|配对可评估|控制错误|投影错误|
|---|---:|---:|---:|
|role_skill|7|6|6|
|state_reading|18|14|9|
|permission|14|9|6|
|team_knowledge|2|2|2|
|public_private|15|5|5|
|night_leak|5|5|5|

public_leak_flag是原有限正则；夜间泄漏由逐题语义审核判断，不能把正则0理解成无泄漏。

## 反事实

{"control": {"pairs": 3, "both_correct": 0, "action_changed": 1}, "treatment": {"pairs": 3, "both_correct": 0, "action_changed": 3}}

只含dev守卫/猎人/狼队三对，不含test对；动作变化本身不代表合理动态调整。以下逐题内容保留配对方向及错误。

## 全部案例（不筛选）

### eval-rule-guard-repeat

角色：guard；night；pair=None。

动作：{"control": {"type": "guard", "target": 12}, "treatment": {"type": "guard", "target": 12}}

mixed：投影后能复述昨夜守12，修正旧回答无技能记录的状态遗漏；但仍执行guard12，并更明确声称守卫重复使用无限制。连守规则未修复，夜间继续公开守护历史和目标。不能把概念关键词命中2/2视为理解正确。

### eval-rule-witch-spent

角色：witch；night；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "pass", "target": null}}

improved：两侧均读到两药耗尽；投影把none改为pass，成为合法且命中参考的弃权。仍夜间公开无药信息，且两侧都把缺信息与不能查验并列，尚不足证明女巫/查验边界被清晰理解；该含混措辞不计作确定技能幻觉的消除。

### eval-rule-witch-current-target

角色：witch；night；pair=None。

动作：{"control": {"type": "save", "target": 12}, "treatment": {"type": "save", "target": 12}}

unchanged：两侧都读到可用解药和当夜刀口12，继续save12而非heal12，严格动作无改善；投影新增需判断是否需查验的含混措辞，没有明确证实角色边界变好。仍提前宣称已救下12并夜间公开刀口/用药。

### eval-rule-hunter-no-permission

角色：hunter；hunter_shot；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：两侧均遵守裁判禁枪但继续none而非pass。投影能读到技能未用，却新增无法发动夜间技能的错误猎人时机描述，并建议已出局玩家等待下一轮。两侧都有公开话语；遗言与技能宣告的边界需分开，不能仅据last_words_allowed=false把宣告一律判为泄漏，该项标未判定。

### eval-rule-vote-dead

角色：villager；exile_vote；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "vote", "target": null}}

improved：控制把不投12归因于身份未确认，投影明确按死亡目标不可投的规则解释，公开回应更切题。但两侧仍输出vote:null，未改成合法pass；严格动作分不变。

### eval-rule-sheriff-withdrawn

角色：villager；sheriff_vote；pair=None。

动作：{"control": {"type": "vote", "target": 12}, "treatment": {"type": "vote", "target": 12}}

improved：投影开始复述自己曾上警退水，公开投票也明确为警长票；比控制遗漏自身报名状态更完整。但仍投12，未理解退水不恢复警徽票权。此处改善仅为状态复述，不能视为权限修复。冻结题目轮次保持原样，未改题。

### eval-rule-parity

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "pass", "target": null}}

mixed：投影把none变为合法pass，减少未知动作词，但两侧均回避3狼对3好人的屠边规则假设，未回答是否立即狼胜。投影公开无发言，比控制泛泛回应更沉默；合法动作改善不等于规则任务完成。

### eval-strategy-silver

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

mixed：投影不再臆列12可能是守夜人这一非Classic角色，也减少了无依据的身份表；但仍错述女巫未确认刀口，未解释被救不能认证阵营/自刀可能，继续none和等待后续信息。存在无关角色措辞减少，策略任务仍未完成，公开回应进一步空泛。

### eval-strategy-vote-change

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "vote", "target": 8}}

regressed：投影能复述12因8补充而改站边，但未分析改判理由是否合理；反而输出vote8并公开称8发言逻辑更合理，同时又说暂不站边。输入没有8补充的具体内容，不能支持该比较。控制虽不消费证据但保持中立，投影出现新增无依据决策和内外矛盾；发言阶段投票仍非法。

### eval-strategy-ambiguous

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "pass", "target": null}}

mixed：投影更准确区分12转述双方完整验人解释与实际认证结果，并把none改成合法pass。仍未提出具体核对问题或当轮判断，公开变为无发言；未达到自主发言任务，不能把弃权合法视为站边能力改善。

### eval-strategy-dead-dark

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "pass", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：两侧均把12的死亡主张与未确认的客观死亡记录区分，未直接采信锁定两狼。投影却从合法pass退为none，仍未解释暗牌死亡不能推出确定剩余狼数。虽恢复了泛泛公开回应，但没有具体追问，未抵消动作接口退步。

### eval-strategy-later-check

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "vote", "target": null}}

unchanged：两侧仍未区分未来警徽流计划调整与篡改已报验人结果，投影还泛称警徽变动可能暗示篡改。动作从none换成vote:null，只减少未知词统计，依旧不合法且不匹配白天发言任务；没有具体核对或解释。

### eval-cf-guard-a

角色：guard；night；pair=guard。

动作：{"control": {"type": "check", "target": 12}, "treatment": {"type": "guard_check", "target": 12}}

regressed：删除checked_seats后仍自称守卫可查验，且把check改为新未知词guard_check；继续忽略last_guard_target=12与禁连守，夜间公开身份和查验目标。无关字段消失没有消除该技能幻觉，接口词反而新增。

### eval-cf-guard-b

角色：guard；night；pair=guard。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "guard", "target": 7}}

mixed：投影从none变为合法guard7，但任务唯一指定目标12，并非自主另选目标。其理由仍把守卫当查验角色，还将上夜守6误述为已查验6；没有学会A禁连守、B可守12的正确反事实关系。夜间继续公开目标。合法动作改善不代表完成任务或技能理解。

### eval-cf-hunter-a

角色：hunter；hunter_shot；pair=hunter。

动作：{"control": {"type": "hunter_shot", "target": 12}, "treatment": {"type": "hunter_shot", "target": 12}}

unchanged：两侧均忽略hunter_can_shoot=false，维持hunter_shot12，并明确声称猎人每轮可查验/执行技能。投影读取尚未使用技能，但把未用等同可用，禁枪权限与角色机制均未修复；两侧仍公开宣告动作；技能宣告与遗言权限不能混算，该题公开泄漏标未判定。

### eval-cf-hunter-b

角色：hunter；hunter_shot；pair=hunter。

动作：{"control": {"type": "hunter_shot", "target": 12}, "treatment": {"type": "shot", "target": 12}}

mixed：投影把猎人查验改成击杀12，技能效果有局部改善；但仍错误声称每轮可击杀一次，并用未知词shot而非shoot。B虽语义选择合法目标，A仍忽略禁枪，整对没有学会权限翻转。public_response仅宣告击杀，与夜间泄漏不同，不能仅凭无遗言权判断宣告违规。

### eval-cf-team-a

角色：werewolf；exile_vote；pair=team。

动作：{"control": {"type": "exile", "target": null}, "treatment": {"type": "vote", "target": 12}}

improved：投影从exile:null变为合法vote12，开始引用1首验矛盾和12改票，公开追问12，优于控制完全不消费公开证据。但A要求因队友1被核实矛盾而调整切割，投影未完成该改变，参考未命中。虽口头称1/4/8已知狼，身份表和策略仍说无证据确认1或当前身份，且全员存活时又不知队友是否存活；队伍确定知识仅局部恢复，仍不一致。

### eval-cf-team-b

角色：werewolf；exile_vote；pair=team。

动作：{"control": {"type": "exile", "target": null}, "treatment": {"type": "exile", "target": null}}

unchanged：投影开始引用1首验一致、改口指控不成立，也修正夜投票措辞，但仍称已知队友1/4/8只是嫌疑、无证据，维持exile:null并泛泛等待。与A组成动作变化（A投12、B无目标），方向没有完成预设切割/维护对照，双题仍不命中；局部公开历史复述不等于稳定队伍知识。

### eval-blind-01

角色：werewolf；day_speech；pair=None。

动作：{"control": {"type": "speech", "target": 1}, "treatment": {"type": "none", "target": null}}

语义审核待完成。

## 证据与限制

原始回答、输入指纹和逐题SHA见本目录cases、run.json、paired_analysis.json及semantic_review.json。skill_state裁剪是一个组合干预（包括序列长度变化），不能区分每个字段的因果贡献。当前权重上的dev结果不能证明训练覆盖或训练日程是唯一主因；后续分支的未执行实验必须明确记为尚未验证。
