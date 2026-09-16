# Training Schedule Diagnostic A vs B_warmup0 正式诊断报告

状态：complete；已比较23/23，语义审核23/23。仅dev探索，非held-out能力验收。

仅取消warmup未让冻结v0.2-core在本组23-dev上学得更有效：出现局部语义变化，但输出结构和动作合法性退化，角色技能/队伍确定知识/夜间信息边界没有稳定修复。B不足以通过继续使用的门禁；按冻结计划，在本报告commit/push后只进入C_accum8，D暂停。

## 实验控制

固定Base/revision、dataset_v0.2、Chat Template、LoRA/NF4及dev生成评分协议；唯一干预来自冻结训练日程矩阵。B仅取消warmup；C若执行则相对B仅accum16改8。A复用已完成v0.2，不重训。每组从同Base开始Rule再接本组Strategy/Tactics，按原验证Loss选择各阶段best/final。使用完全相同的原23条控制输入，包括未当前日程的skill_state；没有使用test调参，没有加入视频或Persona。

## 自动动作指标

strict action score在本报告指合法且命中原参考动作（action_match）；合法动作单列。未知动作token/word指action.type字符串，不是模型词表中的token计数。原严格解析失败的输出不会计入unknown_action_type，另列宽松JSON提取的unknown raw action word，二者不改评分、不做别名纠正。

|指标|控制|当前日程|
|---|---:|---:|
|format_valid|23/23 (100.0%)|15/23 (65.2%)|
|action_legal|3/23 (13.0%)|0/23 (0.0%)|
|action_match|1/23 (4.3%)|0/23 (0.0%)|
|unknown_action_type|14/23 (60.9%)|11/23 (47.8%)|
|public_leak_flag|0/23 (0.0%)|0/23 (0.0%)|
|truncated|0/23 (0.0%)|0/23 (0.0%)|
|unknown_raw_action_word|14/23 (60.9%)|14/23 (60.9%)|
|raw_word_unavailable|0/23 (0.0%)|1/23 (4.3%)|

未知词分布：{"control": {"none": 7, "save": 1, "hunter_shot": 2, "exile": 2, "speech": 2}, "treatment": {"none": 10, "save": 1, "hunter_shot": 2, "exile": 1}}

## 角色分组

|角色/题数|合法 控制→当前日程|严格命中 控制→当前日程|语义变化|
|---|---|---|---|
|guard/4|0→0|0→0|{"mixed": 1, "regressed": 2, "unchanged": 1}|
|hunter/3|0→0|0→0|{"unchanged": 3}|
|seer/1|1→0|1→0|{"regressed": 1}|
|villager/9|1→0|0→0|{"mixed": 3, "regressed": 5, "unchanged": 1}|
|werewolf/4|1→0|0→0|{"mixed": 3, "regressed": 1}|
|witch/2|0→0|0→0|{"unchanged": 1, "regressed": 1}|

## 语义错误复核

下表是模型语义审核，非独立专家盲审；仅统计两侧均可评估的维度，null不按正确计。动作拼写单独评分；语义技能、状态、权限错误依据原回答判定。

|维度|配对可评估|控制错误|当前日程错误|
|---|---:|---:|---:|
|role_skill|9|7|7|
|state_reading|23|18|16|
|permission|17|10|6|
|team_knowledge|4|3|3|
|public_private|20|8|7|
|night_leak|7|7|7|

public_leak_flag是原有限正则；夜间泄漏由逐题语义审核判断，不能把正则0理解成无泄漏。

## 反事实

{"control": {"pairs": 3, "both_correct": 0, "action_changed": 1}, "treatment": {"pairs": 3, "both_correct": 0, "action_changed": 1}}

只含dev守卫/猎人/狼队三对，不含test对；动作变化本身不代表合理动态调整。以下逐题内容保留配对方向及错误。

|配对|控制 A / B|当前日程 A / B|
|---|---|---|
|guard|{"type": "check", "target": 12} / {"type": "none", "target": null}|{"type": "check", "target": 12} / {"type": "none", "target": null}|
|hunter|{"type": "hunter_shot", "target": 12} / {"type": "hunter_shot", "target": 12}|{"type": "hunter_shot", "target": 12} / {"type": "hunter_shot", "target": 12}|
|team|{"type": "exile", "target": null} / {"type": "exile", "target": null}|null / null|

## 全部案例（不筛选）

### eval-rule-guard-repeat

角色：guard；night；pair=None。

动作：{"control": {"type": "guard", "target": 12}, "treatment": {"type": "guard", "target": 12}}

mixed：B能明确复述昨夜守12，修正A的无技能使用记录遗漏；但两侧仍执行非法guard12，B更明确声称技能重复使用无其他限制，并出现暂不需查验的角色混淆措辞。连守规则未修复，夜间公开守护目标仍泄漏。状态读取局部改善不能视为合法决策改善。

### eval-rule-witch-spent

角色：witch；night；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧均读到两药耗尽且不能救人，但仍输出未知动作none，B未转成合法pass。B公开不能救昨夜死者，更贴合题意，但继续夜间泄露药量，并说白天判断是否需要查验，仍有含混的技能边界表达；不足以认定技能理解已修复。核心动作和信息边界缺陷未变。

### eval-rule-witch-current-target

角色：witch；night；pair=None。

动作：{"control": {"type": "save", "target": 12}, "treatment": {"type": "save", "target": 12}}

regressed：两侧都识别当夜刀口12和解药可用，并选择救12，但未知动作save未修正成原协议heal。B新增刀口可能是守夜人的非Classic角色表述，较A泛称狼人或好人的身份边界退步；继续夜间公开救人并声称12已安全，仍把拟执行行动写成确定结果。

### eval-rule-hunter-no-permission

角色：hunter；hunter_shot；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧都读到裁判禁止开枪并没有执行射击，但继续使用未知none而非pass。B补充存活座位却未改善权限到合法动作的映射；仍把出局与禁止开枪并列解释，并承诺后续讨论。猎人技能阶段的宣告不直接当作无遗言权泄漏，public/private维度保持未评估。

### eval-rule-vote-dead

角色：villager；exile_vote；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "vote", "target": null}}

mixed：A以无法确认12身份为主要不投理由；B明确提出避免投死亡玩家，应考虑存活者，死亡目标约束的语义有所改善。但分析仍先说无已知死亡信息，且将死亡玩家不能参与投票与不能被投混在一句，表述不严谨；最终仍是非法vote:null，没有转成原协议pass。保留语义局部改善与执行失败。

### eval-rule-sheriff-withdrawn

角色：villager；sheriff_vote；pair=None。

动作：{"control": {"type": "vote", "target": 12}, "treatment": {"type": "vote", "target": 12}}

regressed：两侧仍忽略自己曾上警退水的历史，错误执行vote12，票权缺陷没有改善。B在身份表中把已知候选12写成可能候选且无直接证据，尽管其他段落承认唯一候选；新增对公开确定事实的内部矛盾，语义略退步。支持警长与证明身份仍未区分清楚。

### eval-rule-parity

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧都忽略三狼一民两神的规则假设，没有回答人数3比3是否立即狼胜或经典屠边条件。B把泛泛观望改成无发言，仍输出未知none。假设问题响应和规则知识调用未改善，不能从未犯出显式错误判断其已掌握胜负规则。

### eval-strategy-silver

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：B省掉A中11/12相关身份分析，也没有解释被救不等于好人；答复缩为无，完全未处理现有公开主张。A有守夜人污染，B虽删除该名称，却新增女巫未查验的技能混淆表述。未知none不变，内容缩短不是更好的信息边界处理。

### eval-strategy-vote-change

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：A至少提到观察12对8的立场调整；B丢失具体改站边线索，仅泛称无信息并回答无。vote:null改为未知none仍不合法；语义上不再试图在发言阶段投票，但没有使用8补充这一新证据完成动态判断，任务响应明显退步。

### eval-strategy-ambiguous

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

mixed：两侧均保留对1/8对跳的谨慎判断，未强行定狼；B删除A对转述者12无依据的神职推测，但未利用双方有完整验人解释来提出具体比较。B把警长与猎人并列为神职信息，新增身份/警徽职务混淆，none和泛泛等待未修复。

### eval-strategy-dead-dark

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "pass", "target": null}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

regressed：两侧都质疑死亡主张与存活状态不符，没有据此锁定狼坑；B身份表seat写成字符串，新增严格结构失败，且把A合法pass改成未知none。保留公开主张核对这一局部能力，但输出协议发生明确退化；未解释暗牌死亡本身不足以确定剩余狼数。

### eval-strategy-later-check

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：B仍未区分警徽流未来计划与已发生查验，也没处理12死亡后的改验逻辑。相较A至少列出6/8相关读人和观察方向，B删除具体对象并回答无，动作仍未知none；策略任务响应变弱。

### eval-cf-guard-a

角色：guard；night；pair=guard。

动作：{"control": {"type": "check", "target": 12}, "treatment": {"type": "check", "target": 12}}

regressed：两侧都把守卫当成查验角色，忽略昨夜守12的连守约束，仍执行check12。B进一步在公开发言编造12身份为守卫且无异常，在没有任何查验结果时捏造技能结果，并与自己守卫身份冲突。夜间泄漏与技能幻觉更严重。

### eval-cf-guard-b

角色：guard；night；pair=guard。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧均忽略last_guard_target=6，声称技能未使用且无查验目标。指定12本可执行guard，B仍因无信息输出未知none并公开守卫身份，角色技能、状态和任务权限理解未改善。

### eval-cf-hunter-a

角色：hunter；hunter_shot；pair=hunter。

动作：{"control": {"type": "hunter_shot", "target": 12}, "treatment": {"type": "hunter_shot", "target": 12}}

unchanged：B原始回答与A逐字相同：仍声称猎人每轮可查验一人，忽略hunter_can_shoot=false，输出未知hunter_shot12并声称查验。取消warmup未改变该反事实禁枪侧的错误。

### eval-cf-hunter-b

角色：hunter；hunter_shot；pair=hunter。

动作：{"control": {"type": "hunter_shot", "target": 12}, "treatment": {"type": "hunter_shot", "target": 12}}

unchanged：两侧都声称猎人只能夜间查验一次，继续输出未知hunter_shot12。B调整了无依据风险描述，却没有修正技能时机/类型；允许开枪侧与禁枪侧最终动作相同，不能证明读取权限后动态改变行动。

### eval-cf-team-a

角色：werewolf；exile_vote；pair=team。

动作：{"control": {"type": "exile", "target": null}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

mixed：B改为投票阶段并在原始action中选择vote1，公开理由引用1的验人矛盾，较A无目标exile有局部任务响应改善。但seat字符串令严格结构失败，不能计作合法/命中；私下仍把已知1/4/8狼人当作待验证嫌疑，strategy还称暂不明确目标，与最终vote1矛盾，不能视为完整狼队切割推理。

### eval-cf-team-b

角色：werewolf；exile_vote；pair=team。

动作：{"control": {"type": "exile", "target": null}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

mixed：B不再称夜投票，修正阶段措辞；但仍将确定队友知识降格为嫌疑，不使用1首验完整一致的新公开证据来调整目标。最终exile:null不变，且新增seat字符串结构错误。与A侧原始动作出现差异，只能算局部响应变化，原严格反事实双正确仍未达到。

### eval-blind-01

角色：werewolf；day_speech；pair=None。

动作：{"control": {"type": "speech", "target": 1}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

mixed：B在wolf_pit和身份表明确1/4/8是狼人，改善A对1确定知识的降格，也未再声称团队已公开暴露。但无依据把2/5/9定为普通村民，忽略当前逼问与记录冲突，策略称避免攻击却在发言阶段vote1；seat字符串新增格式失败，公开回答仍照抄对自己的问题。确定知识局部恢复伴随执行和视角任务失败。

### eval-blind-02

角色：werewolf；sheriff_speech；pair=None。

动作：{"control": {"type": "pass", "target": null}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

regressed：A的身份表和wolf_pit保留1/4/8确定狼队知识；B明确说高概率且未验证，确定知识退化。原始pass虽仍存在，却因seat字符串导致严格格式/合法动作失分；仍未利用8被认可的局面规划狼队发言，只有等待。

### eval-blind-04

角色：seer；night；pair=None。

动作：{"control": {"type": "check", "target": 12}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

regressed：B保留原始check12及站边冲突依据，但seat字符串令结构失败，失去A唯一strict action命中；分析把当前夜间行动说成下一轮查验，时点表述变差。夜间公开目标仍泄漏。冻结题目原本含先选择12提示，此处不能把原始选12当作自主选人提升。

### eval-blind-05

角色：guard；night；pair=None。

动作：{"control": {"type": "guard", "target": 12}, "treatment": {"parse_error": "Expecting ':' delimiter: line 17 column 19 (char 373)"}}

regressed：两侧均无视昨夜已守12，继续把守卫与查验混淆，原始动作仍非法guard12且夜间公开目标。B新增JSON缺少键值分隔的语法错误；自己为守卫却猜6可能守卫，神职唯一性也不稳。守卫核心技能和执行协议均未修复。

### eval-blind-07

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "speech", "target": null}, "treatment": {"parse_error": "invalid identity seat/assessment"}}

mixed：B准确复述互不信任、互攻却同票，改善A分析中的互信误读；但seat字符串导致结构失败，speech改为未知none，公开回答从A的具体追问退为无。新证据理解局部改善没有落实到当前发言决策。

## 已证实

- B真实6 optimizer步/6非零LR步，A为6/3；每阶段B LR=[5e-5,2.5e-5]，所有best=step2且final相同，实际张量发生变化。
- 同23-dev严格结构23→15、合法动作3→0、严格命中1→0；反事实双正确0/3→0/3，无截断。
- 8个结构失败包括7个identity seat字符串和1个JSON语法错误；不能用修改评分或修正输出来追回分数。

## 有支持证据

- 日程改变会改变此模型的输出行为：部分状态/权限表述改善，同时出现结构退化和更少的具体策略回应。
- 7个mixed、6个unchanged、10个regressed；没有无伴随退化的整体improved案例。语义是模型复核而非独立人工盲评。

## 暂不支持

- 仅取消warmup足以稳定修复Classic核心能力。Loss下降不足以证明技能学会。
- unknown_action_type从14降11不代表动作词改善：格式失败先被拒绝；宽松JSON读取未知词仍14个，另1个JSON语法错误无法读取。
- 技能错误配对统计7/9→7/9、队伍知识3/4→3/4、夜漏7/7→7/7，不支持稳定核心能力改善。

## 尚未验证

- 当前失败是否主要由更新次数过少引起；C_accum8和D_epochs2尚未实际执行。
- 阶段间遗忘、更多epoch、多个随机种子及held-out泛化；不得解锁test、视频、Persona或v0.3。
- B同时改变cosine LR轨迹、积分和Adam历史；无法单独归因于有效步数。

## 证据与限制

原始回答、输入指纹和逐题SHA见本目录cases、run.json、paired_analysis.json及semantic_review.json。取消warmup使B每阶段LR从[0,5e-5]变为[5e-5,2.5e-5]，也改变总LR积分与Adam更新轨迹；A的零LR步仍积累动量。不能把结果归因于单独的更新次数，也不能证明整个失败已解释。只有单种子和反复诊断的23-dev，不支持held-out泛化结论。后续未执行实验明确记为尚未验证。

角色技能错误包含明确的错误角色/技能规则；state_reading包括相关状态、公开历史和任务信息使用；permission关注语义权限，不把未知动作拼写直接当作不懂权限。维度可重叠，不相加作为总错误数。mixed表示同题同时有局部改善与退步/主要缺陷持续。语义等级是模型复核，不是独立人工评分。

Blind-04的冻结公开资料包含本次比较先选择12，因此其命中不能独立证明无目标提示的自主决策。保持题目原样来控制实验，不对已有分数追溯修改。
